"""Stable asset identity, append-only placement and versioned typed configuration."""
import json,re,hashlib
from contextlib import contextmanager
from decimal import Decimal,InvalidOperation
from datetime import date
import frappe
from frappe.utils import now_datetime,get_datetime,cint
from vanbags_maintenance import organization as org,teams
from vanbags_maintenance.work_contract import atomic
EQ='VB Equipment'
INSTALL='TruCMMS Equipment Installation'
EVENT='TruCMMS Asset Event'
PROFILE='TruCMMS Equipment Profile'
CRIT='TruCMMS Criticality'

@contextmanager
def controlled():
    prior=frappe.flags.get('trucmms_asset_write');frappe.flags.trucmms_asset_write=True
    try:yield
    finally:frappe.flags.trucmms_asset_write=prior

def manager():
    if not org.privileged() and 'VB Maintenance Manager' not in frappe.get_roles():frappe.throw('Equipment manager required.',frappe.PermissionError)

def company_lock(company):
    teams.locked_sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE',(company,))

def reason_required(reason):
    reason=(reason or '').strip()
    if not reason:frappe.throw('A reason is required.')
    return reason

def stamp(value=None):
    result=get_datetime(value) if value else now_datetime()
    if result.tzinfo is not None:frappe.throw('Use a system-time Datetime through the native Frappe conversion.')
    if result>now_datetime():frappe.throw('Future placement is not supported; record the effective movement when it occurs.')
    return result

def current(doc):
    rows=teams.locked_sql(f'SELECT * FROM `tab{INSTALL}` WHERE equipment=%s AND effective_until IS NULL FOR UPDATE',(doc.name,),as_dict=True)
    if len(rows)>1:frappe.throw('Multiple active placements require administrative reconciliation.')
    return frappe.get_doc({'doctype':INSTALL,**rows[0]}) if rows else None

def attributes(doc):
    return [(r.key,r.value,r.value_type,r.unit or '') for r in doc.get('attributes',[])]

def validate_equipment(doc):
    old=doc.get_doc_before_save();writing=frappe.flags.get('trucmms_asset_write')
    if not doc.company or not doc.site:frappe.throw('Company and Site are required.')
    if not old:
        if doc.placement_policy not in (None,'','D1'):frappe.throw('New equipment must use the current placement policy.')
        doc.placement_policy='D1';company_lock(doc.company)
        capacity(doc.company,doc.site,doc.location,doc.name)
    else:
        if doc.placement_policy!=old.placement_policy and not writing:frappe.throw('Use explicit placement adoption.')
        if (doc.site,doc.location)!=(old.site,old.location) and not writing:frappe.throw('Use the controlled placement action to preserve location history.')
        fields=('asset_tag','tag_key','technical_profile','profile_snapshot','criticality','criticality_snapshot')
        if (any(doc.get(k)!=old.get(k) for k in fields) or attributes(doc)!=attributes(old)) and not writing:frappe.throw('Use Configure Asset with a reason to change tags, profiles, attributes or criticality.')
    tag=' '.join((doc.asset_tag or '').strip().upper().split())
    if tag and not re.fullmatch(r'[A-Z0-9][A-Z0-9 ._:/-]{0,79}',tag):frappe.throw('Asset Tag must be 1-80 letters, digits, spaces or ._:/- characters.')
    expected=hashlib.sha256((doc.company+'|'+tag).encode()).hexdigest() if tag else None
    if not old and doc.tag_key:frappe.throw('Tag identity is server controlled.')
    doc.asset_tag=tag;doc.tag_key=expected
    if not old or writing:
        configure_values(doc,old)

def validate_profile(doc):
    old=doc.get_doc_before_save()
    if not re.fullmatch(r'[A-Z0-9._-]{1,80}',doc.code or '') or cint(doc.version)<1:frappe.throw('Use an uppercase profile code and a positive version.')
    keys=set()
    for row in doc.definitions:
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,49}',row.key or '') or row.key in keys:frappe.throw('Attribute keys must be unique lowercase identifiers.')
        keys.add(row.key)
        if row.value_type not in ('Text','Integer','Decimal','Date','Boolean','Choice'):frappe.throw('Unsupported attribute type.')
        bounds=[]
        for field in ('minimum','maximum'):
            value=row.get(field)
            if value not in (None,''):
                if row.value_type not in ('Integer','Decimal'):frappe.throw('Only numeric attributes support bounds.')
                number=decimal(value)
                if row.value_type=='Integer' and number!=number.to_integral_value():frappe.throw('Integer bounds must be integers.')
                bounds.append(number)
        if len(bounds)==2 and bounds[0]>bounds[1]:frappe.throw('Minimum cannot exceed maximum.')
        choices=(row.choices or '').splitlines()
        if row.value_type=='Choice' and (not choices or any(not x.strip() or x!=x.strip() for x in choices) or len(choices)!=len(set(choices))):frappe.throw('Choice values must be nonempty and unique, one per line.')
        if row.value_type!='Choice' and row.choices:frappe.throw('Choices apply only to Choice attributes.')
    if not keys:frappe.throw('Define at least one typed attribute.')
    if old:
        fields=('key','label','value_type','unit','required','minimum','maximum','choices')
        before=[tuple(r.get(k) for k in fields) for r in old.definitions];after=[tuple(r.get(k) for k in fields) for r in doc.definitions]
        if before!=after or (old.code,old.version)!=(doc.code,doc.version):frappe.throw('Profile definitions are immutable; create a new version with a new code.')

def validate_criticality(doc):
    old=doc.get_doc_before_save()
    if not re.fullmatch(r'[A-Z0-9._-]{1,80}',doc.code or '') or cint(doc.rank)<1:frappe.throw('Use an uppercase criticality code and positive rank.')
    if old and any(old.get(k)!=doc.get(k) for k in ('code','rank','criticality_name','description')):frappe.throw('Criticality definitions are immutable; create a new code.')

def decimal(value):
    try:result=Decimal(str(value))
    except (InvalidOperation,ValueError):frappe.throw('Invalid numeric attribute.')
    if not result.is_finite() or result.copy_abs()>Decimal('1e20'):frappe.throw('Numeric attributes must be finite and within supported bounds.')
    if result.as_tuple().exponent < -12 or len(result.as_tuple().digits)>32:frappe.throw('Numeric attributes support at most 12 decimal places and 32 significant digits.')
    return result

def typed(value,definition):
    text=str(value).strip();kind=definition['value_type']
    if len(text)>5000:frappe.throw('Attribute value is too long.')
    if kind in ('Integer','Decimal'):
        number=decimal(text)
        if kind=='Integer' and number!=number.to_integral_value():frappe.throw('An integer attribute requires a whole number.')
        for field,valid in [('minimum',lambda x:number>=x),('maximum',lambda x:number<=x)]:
            if definition.get(field) not in (None,'') and not valid(decimal(definition[field])):frappe.throw('Numeric attribute is outside profile bounds.')
        text=str(int(number)) if kind=='Integer' else format(number,'f')
    elif kind=='Boolean':
        if text not in ('0','1'):frappe.throw('Boolean attributes require 0 or 1.')
    elif kind=='Date':
        try:
            if date.fromisoformat(text).isoformat()!=text:raise ValueError()
        except ValueError:frappe.throw('Date attributes require YYYY-MM-DD.')
    elif kind=='Choice' and text not in (definition.get('choices') or '').splitlines():frappe.throw('Attribute value is not an allowed choice.')
    return text

def configure_values(doc,old):
    changed=not old or old.technical_profile!=doc.technical_profile
    if changed:
        if not old and doc.profile_snapshot:frappe.throw('Profile snapshots are server controlled.')
        if doc.technical_profile:
            profile=frappe.get_doc(PROFILE,doc.technical_profile);profile.check_permission('read')
            if profile.disabled:frappe.throw('Cannot assign a disabled profile.')
            schema={'profile':profile.name,'version':profile.version,'definitions':[{k:r.get(k) for k in ('key','label','value_type','unit','required','minimum','maximum','choices')} for r in profile.definitions]}
            doc.profile_snapshot=json.dumps(schema,sort_keys=True)
        else:doc.profile_snapshot=None
    elif old:doc.profile_snapshot=old.profile_snapshot
    if doc.profile_snapshot:
        definitions={r['key']:r for r in json.loads(doc.profile_snapshot)['definitions']};seen=set()
        for row in doc.attributes:
            if row.key not in definitions or row.key in seen:frappe.throw('Unknown or duplicate profile attribute.')
            seen.add(row.key);definition=definitions[row.key]
            if row.value in (None,''):frappe.throw('Remove empty optional values or supply the required value.')
            row.value=typed(row.value,definition);row.value_type=definition['value_type'];row.unit=definition.get('unit') or ''
        if any(r['required'] and key not in seen for key,r in definitions.items()):frappe.throw('Required profile attributes are missing.')
    elif doc.attributes:frappe.throw('Choose a technical profile before adding attributes.')
    if not old or old.criticality!=doc.criticality:
        if not old and doc.criticality_snapshot:frappe.throw('Criticality snapshots are server controlled.')
        if doc.criticality:
            value=frappe.get_doc(CRIT,doc.criticality);value.check_permission('read')
            if value.disabled:frappe.throw('Cannot assign a disabled criticality.')
            doc.criticality_snapshot=json.dumps({k:value.get(k) for k in ('code','criticality_name','rank','description')},sort_keys=True)
        else:doc.criticality_snapshot=None
    elif old:doc.criticality_snapshot=old.criticality_snapshot

def context(company,site,location=None,exclude=None):
    target=frappe.get_doc('TruCMMS Site',site);target.check_permission('read')
    if target.company!=company or target.disabled:frappe.throw('Choose an active site in the same Company.')
    if location:
        place=frappe.get_doc('VB Equipment Location',location);place.check_permission('read')
        if place.company!=company or place.site!=site or place.disabled:frappe.throw('Choose an active functional location in the target site.')
        capacity(company,site,location,exclude)

def insert_placement(doc,when,reason,kind):
    context(doc.company,doc.site,doc.location,doc.name)
    # Creation already contains its own equipment row; exclude that row for capacity.
    with controlled():
        return frappe.get_doc({'doctype':INSTALL,'equipment':doc.name,'company':doc.company,'site':doc.site,'location':doc.location,'effective_from':when,'recorded_on':now_datetime(),'recorded_by':frappe.session.user,'reason':reason,'entry_type':kind}).insert(ignore_permissions=True)

def initialize_placement(doc,reason='Initial declared placement; no earlier installation history inferred',kind='Initial',when=None):
    if doc.placement_policy!='D1':return
    # Capacity is checked before insertion while holding the Company lock.
    with controlled():
        frappe.get_doc({'doctype':INSTALL,'equipment':doc.name,'company':doc.company,'site':doc.site,'location':doc.location,'effective_from':when or now_datetime(),'recorded_on':now_datetime(),'recorded_by':frappe.session.user,'reason':reason,'entry_type':kind}).insert(ignore_permissions=True)

def lock_equipment(name):
    manager();company=frappe.db.get_value(EQ,name,'company')
    if not company:frappe.throw('Equipment not found.',frappe.DoesNotExistError)
    company_lock(company);doc=teams.locked_document(EQ,name);doc.check_permission('write');return doc

def no_open_work(doc,when=None):
    rows=teams.locked_sql("SELECT name FROM `tabTruCMMS Maintenance Work Order` WHERE equipment=%s AND status NOT IN ('Closed','Cancelled') LIMIT 1 FOR UPDATE",(doc.name,))
    if rows:frappe.throw('Close or cancel open work orders before relocating/removing this equipment.')
    if when:
        for dt in ('TruCMMS Maintenance Work Order','TruCMMS Maintenance Request'):
            latest=teams.locked_sql(f'SELECT modified FROM `tab{dt}` WHERE equipment=%s ORDER BY modified DESC LIMIT 1 FOR UPDATE',(doc.name,),as_dict=True)
            if latest and when<get_datetime(latest[0].modified):frappe.throw('Movement cannot be backdated across existing work activity.')

def event(doc,action,reason,when,before):
    old_site=before.get('site')
    with controlled():
        frappe.get_doc({'doctype':EVENT,'equipment':doc.name,'company':doc.company,'site':doc.site,'other_site':old_site if old_site!=doc.site else None,'action':action,'reason':reason,'effective_on':when,'recorded_on':now_datetime(),'recorded_by':frappe.session.user,'before_snapshot':json.dumps(asset_snapshot(before),default=str),'after_snapshot':json.dumps(asset_snapshot(doc.as_dict()),default=str)}).insert(ignore_permissions=True)

def close_placement(doc,when,reason):
    row=current(doc)
    if row:
        if when<=get_datetime(row.effective_from):frappe.throw('Movement must be later than the previous placement start.')
        row.effective_until=when;row.ended_on=now_datetime();row.ended_by=frappe.session.user;row.end_reason=reason
        with controlled():row.save(ignore_permissions=True)
    else:
        last=teams.locked_sql(f'SELECT effective_until FROM `tab{INSTALL}` WHERE equipment=%s ORDER BY effective_from DESC LIMIT 1 FOR UPDATE',(doc.name,),as_dict=True)
        if last and last[0].effective_until and when<get_datetime(last[0].effective_until):frappe.throw('Movement cannot precede the last removal.')
    return row

@frappe.whitelist(methods=['POST'])
@atomic
def adopt(equipment,reason):
    doc=lock_equipment(equipment);reason=reason_required(reason)
    if doc.placement_policy!='Legacy':frappe.throw('Only legacy equipment needs placement adoption.')
    before=doc.as_dict();when=now_datetime()
    # Capacity includes legacy equipment, excluding the equipment being declared.
    capacity(doc.company,doc.site,doc.location,doc.name)
    with controlled():
        doc.placement_policy='D1';doc.save();initialize_placement(doc,reason,'Declared Baseline',when)
    event(doc,'Declare Baseline',reason,when,before);return doc.as_dict()

def capacity(company,site,location,exclude=None):
    if not location:return
    place=frappe.get_doc('VB Equipment Location',location)
    if place.single_equipment:
        rows=teams.locked_sql(f'SELECT name FROM `tab{EQ}` WHERE company=%s AND location=%s AND name!=%s FOR UPDATE',(company,location,exclude or ''),pluck=True)
        if rows:frappe.throw('This single-equipment position is occupied.')

@frappe.whitelist(methods=['POST'])
@atomic
def place(equipment,site,location=None,reason=None,effective_on=None):
    doc=lock_equipment(equipment);reason=reason_required(reason);when=stamp(effective_on);location=location or None
    if doc.placement_policy!='D1':frappe.throw('Declare the legacy baseline before moving equipment.')
    if (doc.site,doc.location or None)==(site,location) and current(doc):frappe.throw('Equipment already has this active placement.')
    no_open_work(doc,when)
    if doc.status=='Retired':frappe.throw('Retired equipment cannot receive a new placement.')
    context(doc.company,site,location)
    before=doc.as_dict();close_placement(doc,when,reason)
    with controlled():
        doc.site=site;doc.location=location;doc.save();insert_placement(doc,when,reason,'Transfer' if before['site']!=site else 'Install')
    event(doc,'Place Equipment',reason,when,before);return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def remove(equipment,reason,effective_on=None):
    doc=lock_equipment(equipment);reason=reason_required(reason);when=stamp(effective_on)
    if doc.placement_policy!='D1' or not current(doc):frappe.throw('An active managed placement is required.')
    no_open_work(doc,when);before=doc.as_dict();close_placement(doc,when,reason)
    with controlled():doc.location=None;doc.save()
    event(doc,'Remove Equipment',reason,when,before);return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def replace(equipment,replacement,reason,effective_on=None):
    if equipment==replacement:frappe.throw('Choose a different replacement equipment.')
    first=lock_equipment(equipment);other_company=frappe.db.get_value(EQ,replacement,'company')
    if other_company!=first.company:frappe.throw('Replacement must belong to the same Company.')
    second=lock_equipment(replacement);reason=reason_required(reason);when=stamp(effective_on)
    if first.placement_policy!='D1' or second.placement_policy!='D1' or not first.location:frappe.throw('Replacement requires managed equipment and a fixed occupied location.')
    if second.site!=first.site or second.location:frappe.throw('Replacement must be uninstalled and held at the same site.')
    no_open_work(first,when);no_open_work(second,when)
    if second.status=='Retired':frappe.throw('Retired equipment cannot replace active equipment.')
    before_first=first.as_dict();before_second=second.as_dict();location=first.location
    close_placement(first,when,reason);close_placement(second,when,reason)
    with controlled():
        first.location=None;first.save();second.location=location;second.save();insert_placement(second,when,reason,'Replacement')
    event(first,'Replaced Equipment',reason,when,before_first);event(second,'Replacement Installed',reason,when,before_second)
    return {'removed':first.name,'installed':second.name}

@frappe.whitelist(methods=['POST'])
@atomic
def configure(equipment,reason,asset_tag=None,technical_profile=None,values=None,criticality=None):
    doc=lock_equipment(equipment);reason=reason_required(reason);before=doc.as_dict()
    # This action supplies the complete intended configuration, including explicit clearing.
    doc.asset_tag=asset_tag;doc.technical_profile=technical_profile;doc.criticality=criticality
    values=frappe.parse_json(values) if isinstance(values,str) else values
    if values is not None and not isinstance(values,dict):frappe.throw('Attribute values must be an object keyed by profile attribute.')
    doc.set('attributes',[{'key':k,'value':str(v)} for k,v in (values or {}).items()])
    with controlled():doc.save()
    event(doc,'Configure Asset',reason,now_datetime(),before);return doc.as_dict()

def validate_location(doc,method=None):
    old=doc.get_doc_before_save()
    if old and cint(old.single_equipment)!=cint(doc.single_equipment) and not frappe.flags.get('trucmms_asset_write'):frappe.throw('Use Configure Position to change occupancy policy with a reason.')

@frappe.whitelist(methods=['POST'])
@atomic
def configure_position(location,single_equipment,reason):
    manager();company=frappe.db.get_value('VB Equipment Location',location,'company');company_lock(company)
    doc=teams.locked_document('VB Equipment Location',location);doc.check_permission('write');reason=reason_required(reason)
    if str(single_equipment) not in ('0','1'):frappe.throw('Choose 0 or 1 for single equipment.')
    if cint(single_equipment):
        rows=teams.locked_sql(f'SELECT name FROM `tab{EQ}` WHERE company=%s AND location=%s FOR UPDATE',(company,location),pluck=True)
        if len(rows)>1:frappe.throw('Reconcile existing occupancy before enabling a single-equipment position.')
    before={'single_equipment':cint(doc.single_equipment)}
    with controlled():
        doc.single_equipment=cint(single_equipment);doc.save()
        frappe.get_doc({'doctype':EVENT,'company':doc.company,'site':doc.site,'location':doc.name,'action':'Configure Position','reason':reason,'effective_on':now_datetime(),'recorded_on':now_datetime(),'recorded_by':frappe.session.user,'before_snapshot':json.dumps(before),'after_snapshot':json.dumps({'single_equipment':cint(doc.single_equipment)})}).insert(ignore_permissions=True)
    return doc.as_dict()

def history_permission(doc,user=None,ptype=None):
    if ptype not in (None,'read','select','report'):frappe.throw('Asset history is read only.',frappe.PermissionError)
    org.has_permission(doc,user,ptype)
    if doc.doctype==EVENT and doc.other_site and not org.privileged(user):
        probe=frappe._dict(doctype=EVENT,company=doc.company,site=doc.other_site)
        if not org.in_scope(probe,user):frappe.throw('Both movement sites must be authorized.',frappe.PermissionError)
    return True

def installation_query(user=None):return org.query(INSTALL,user)
def event_query(user=None):
    condition=org.query(EVENT,user)
    if not condition:return ''
    companies,sites=org.allowed(EVENT,user)
    allowed=','.join(frappe.db.escape(s) for s in sites) or "''"
    return condition+f" AND (COALESCE(`tab{EVENT}`.other_site,'')='' OR `tab{EVENT}`.other_site IN ({allowed}))"

def validate_share(doc,method=None):
    if doc.share_doctype in (INSTALL,EVENT):
        if doc.everyone:frappe.throw('Asset history cannot be public.',frappe.PermissionError)
        history_permission(frappe.get_doc(doc.share_doctype,doc.share_name),doc.user,'read')

def setup():
    from vanbags_maintenance import work_cycle,configuration
    work_cycle.setup(record=False)
    frappe.db.sql("UPDATE `tabVB Equipment` SET placement_policy='Legacy' WHERE COALESCE(placement_policy,'')=''")
    frappe.db.add_index(INSTALL,['equipment','effective_until'],'equipment_active_placement')
    frappe.db.add_index(INSTALL,['company','site','location','effective_from'],'position_history')
    configuration.record_deployment()


def installation_register(filters=None):
    f=frappe._dict(filters or {})
    if not frappe.has_permission(INSTALL,'report'):frappe.throw('Installation report permission required.',frappe.PermissionError)
    filters={k:f[k] for k in ('company','site','equipment','location') if f.get(k)}
    if f.get('as_of'):
        when=get_datetime(f.as_of);filters['effective_from']=['<=',when]
        rows=frappe.get_list(INSTALL,filters=filters,fields=['name','equipment','company','site','location','effective_from','effective_until','entry_type','recorded_on','recorded_by'],limit_page_length=0,order_by='effective_from desc')
        rows=[r for r in rows if not r.effective_until or get_datetime(r.effective_until)>when]
    else:
        if cint(f.get('active_only')):filters['effective_until']=['is','not set']
        rows=frappe.get_list(INSTALL,filters=filters,fields=['name','equipment','company','site','location','effective_from','effective_until','entry_type','recorded_on','recorded_by'],limit_page_length=0,order_by='effective_from desc')
    columns=[dict(fieldname=n,label=l,fieldtype=t,options=o,width=w) for n,l,t,o,w in [
        ('name','Installation','Link',INSTALL,170),('equipment','Equipment','Link',EQ,160),('company','Company','Link','Company',150),('site','Site','Link','TruCMMS Site',150),('location','Functional Location','Link','VB Equipment Location',170),('entry_type','Entry Type','Data',None,140),('effective_from','Effective From','Datetime',None,170),('effective_until','Effective Until','Datetime',None,170),('recorded_on','Recorded On','Datetime',None,170),('recorded_by','Recorded By','Link','User',180)]]
    return columns,rows,'Intervals include the start and exclude the end. Blank location means mobile/site custody. Declared baselines do not establish earlier installation history.'


def validate_work_equipment(doc):
    if not doc.equipment:return
    equipment=teams.locked_document(EQ,doc.equipment);equipment.check_permission('read')
    if equipment.company!=doc.company or equipment.site!=doc.site:frappe.throw('Equipment must currently belong to the work Company and Site.')
    return equipment

def work_snapshot(doc):
    old=doc.get_doc_before_save()
    if old:
        if old.get('equipment_snapshot')!=doc.get('equipment_snapshot'):frappe.throw('Historical equipment context is server controlled.')
        return
    if doc.get('equipment_snapshot'):frappe.throw('Historical equipment context is server controlled.')
    equipment=validate_work_equipment(doc)
    if equipment:
        fields=('name','equipment_code','asset_tag','equipment_name','company','site','location','manufacturer','model','serial_number','technical_profile','profile_snapshot','criticality','criticality_snapshot')
        value={k:equipment.get(k) for k in fields};value['attributes']=[{k:r.get(k) for k in ('key','value','value_type','unit')} for r in equipment.attributes]
        doc.equipment_snapshot=json.dumps(value,sort_keys=True,default=str)


def asset_snapshot(values):
    fields=('name','equipment_code','equipment_name','asset_tag','company','site','location','status','category','manufacturer','model','serial_number','technical_profile','profile_snapshot','criticality','criticality_snapshot','placement_policy')
    result={k:values.get(k) for k in fields}
    result['attributes']=[{k:row.get(k) for k in ('key','value','value_type','unit')} for row in values.get('attributes',[])]
    return result
