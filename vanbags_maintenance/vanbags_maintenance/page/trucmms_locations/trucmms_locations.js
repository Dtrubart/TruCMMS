frappe.pages['trucmms-locations'].on_page_load = function (wrapper) {
 const page = frappe.ui.make_app_page({parent: wrapper, title: __('Ubicaciones funcionales'), single_column: true});
 const root = $('<div class="trucmms-locations"></div>').appendTo(page.body);
 $('<style>').text('.trucmms-locations .location-grid{display:grid;grid-template-columns:minmax(250px,1fr) minmax(300px,2fr);gap:24px;margin-top:20px}.trucmms-locations .location-panel{min-width:0;overflow-wrap:anywhere}.trucmms-locations .btn{min-height:44px;margin:4px}.trucmms-locations .location-crumbs{padding:12px 0}.trucmms-locations .location-event{border-top:1px solid var(--border-color);padding:10px 0}@media(max-width:700px){.trucmms-locations .location-grid{grid-template-columns:1fr}}').appendTo(root);
 const notice = $('<div role="status" aria-live="polite"></div>').appendTo(root);
 const grid = $('<div class="location-grid"></div>').appendTo(root);
 const browser = $('<section class="location-panel"></section>').appendTo(grid);
 const detail = $('<section class="location-panel"></section>').appendTo(grid);
 let ready = false, sequence = 0, detailSequence = 0, selected = null, tree = null;
 const company = page.add_field({fieldname: 'company', label: __('Empresa'), fieldtype: 'Link', options: 'Company',
  change: () => { if (ready) { site.set_value(''); load(); } }});
 const site = page.add_field({fieldname: 'site', label: __('Sede'), fieldtype: 'Link', options: 'TruCMMS Site',
  get_query: () => ({filters: company.get_value() ? {company: company.get_value()} : {}}), change: () => ready && load()});
 const search = page.add_field({fieldname: 'search', label: __('Buscar ubicación'), fieldtype: 'Data', change: () => ready && load()});
 function options() { return Object.fromEntries([['site', site.get_value()], ['company', company.get_value()]].filter(([, value]) => value)); }
 function button(parent, label, action) {
  return $('<button type="button" class="btn btn-default"></button>').text(__(label)).appendTo(parent).on('click', action);
 }
 function list(dt, filters) { frappe.route_options = filters; frappe.set_route('List', dt); }
 async function show(name) {
  const request = ++detailSequence, context = sequence;
  detail.empty(); selected = null;
  const {message: doc} = await frappe.call({method: 'vanbags_maintenance.location_hierarchy.details', type: 'GET', args: {name}});
  if (request !== detailSequence || context !== sequence) return;
  if (doc.site !== site.get_value() || (company.get_value() && doc.company !== company.get_value())) {
   notice.text(__('La ubicación no pertenece al contexto seleccionado.')); return;
  }
  selected = doc;
  const crumbs = $('<nav class="location-crumbs" aria-label="Ubicación"></nav>').appendTo(detail);
  doc.path.forEach((node, index) => {
   if (index) $('<span></span>').text(' / ').appendTo(crumbs);
   button(crumbs, node.label, () => show(node.name));
  });
  $('<h3></h3>').text(doc.label).appendTo(detail);
  $('<p></p>').text(doc.site + ' · ' + doc.company + (doc.disabled ? ' · ' + __('Desactivada') : '')).appendTo(detail);
  button(detail, 'Abrir ficha', () => frappe.set_route('Form', 'VB Equipment Location', doc.name));
  if (doc.can_write) button(detail, 'Cambiar jerarquía / estado', () => {
   if (doc !== selected) return;
   frappe.trucmms_location_change(doc.name, doc.company, doc.site, async () => { await load(); show(doc.name); });
  });
  const scope = {company: doc.company, site: doc.site};
  if (frappe.model.can_read('VB Equipment')) button(detail, 'Equipos en esta ubicación', () => list('VB Equipment', {...scope, location: doc.name}));
  if (frappe.model.can_read('TruCMMS Measurement Point')) button(detail, 'Puntos de medición', () => list('TruCMMS Measurement Point', {...scope, functional_location: doc.name}));
  if (frappe.model.can_read('TruCMMS Maintenance Request')) button(detail, 'Solicitudes de esta ubicación', () => list('TruCMMS Maintenance Request', {...scope, functional_location: doc.name}));
  if (frappe.model.can_read('TruCMMS Maintenance Work Order')) button(detail, 'Órdenes con alcance aquí', () => list('TruCMMS Maintenance Work Order', {...scope, scope_location: doc.name}));
  $('<p class="text-muted"></p>').text(__('Estos accesos filtran la ubicación exacta; no incluyen descendientes ni todos los puntos secundarios de una orden.')).appendTo(detail);
  if (!doc.disabled && frappe.model.can_create('VB Equipment Location')) button(detail, 'Crear ubicación hija', () => frappe.new_doc('VB Equipment Location', {...scope, parent_location: doc.name}));
  $('<h4></h4>').text(__('Historial registrado')).appendTo(detail);
  $('<p class="text-muted"></p>').text(__('Las ubicaciones existentes conservan su historial anterior. Aquí se mostrarán sus próximos cambios de jerarquía.')).appendTo(detail);
  if (!doc.events.length) $('<p></p>').text(__('Sin eventos de jerarquía registrados.')).appendTo(detail);
  for (const event of doc.events) {
   const row = $('<div class="location-event"></div>').appendTo(detail);
   $('<strong></strong>').text(event.action).appendTo(row);
   $('<div></div>').text(event.reason).appendTo(row);
   $('<small></small>').text(event.effective_on + ' · ' + event.recorded_by).appendTo(row);
  }
  if (doc.more_events) button(detail, 'Ver historial completo', () => list('TruCMMS Location Event', {location: doc.name}));
 }
 async function load() {
  const request = ++sequence; ++detailSequence; selected = null; tree = null;
  browser.empty(); detail.empty();
  if (!site.get_value()) { notice.text(__('Selecciona una sede autorizada.')); return; }
  notice.text(__('Cargando ubicaciones…'));
  const args = options(), query = search.get_value().trim();
  try {
   if (query) {
    async function results(start = 0) {
     const {message: data} = await frappe.call({method: 'vanbags_maintenance.location_hierarchy.children', type: 'GET', args: {...args, search: query, start}});
     if (request !== sequence) return;
     browser.empty();
     for (const row of data.rows) button(browser, row.location_name + (row.disabled ? ' · ' + __('Desactivada') : ''), () => show(row.name));
     if (start) button(browser, 'Anterior', () => results(Math.max(0, start - data.limit)));
     if (data.more) button(browser, 'Siguiente', () => results(start + data.limit));
     notice.text(data.rows.length ? __('Resultados de esta sede') : __('Sin resultados'));
    }
    await results(); return;
   }
   if (request !== sequence) return;
   const pages = {}, offsets = {}, pending = {}, pagerPrefix = '__trucmms_more__';
   class LocationTree extends frappe.ui.Tree {
    async get_nodes(value, is_root) {
     const parent = is_root ? '' : value;
     if (pending[parent]) return pending[parent];
     pending[parent] = this.fetch_nodes(parent);
     try { return await pending[parent]; } finally { delete pending[parent]; }
    }
    async fetch_nodes(parent) {
     const {message: data} = await frappe.call({method: 'vanbags_maintenance.location_hierarchy.children', type: 'GET', args: {...args, parent, start: offsets[parent] || 0}});
     if (request !== sequence) return [];
     const nodes = data.rows.map(row => ({value: row.name, title: row.location_name + (row.disabled ? ' · ' + __('Desactivada') : ''), expandable: row.expandable}));
     pages[parent] = [...(pages[parent] || []), ...nodes];
     return [...pages[parent], ...(data.more ? [{value: pagerPrefix + parent, title: __('Cargar más'), expandable: 0, page_parent: parent, next: (offsets[parent] || 0) + data.limit}] : [])];
    }
   }
   tree = new LocationTree({parent: browser, label: site.get_value(), root_value: '__trucmms_root__', expandable: true, with_skeleton: false,
    on_click(node) {
     if (request !== sequence || node.is_root) return;
     if (Object.hasOwn(node.data, 'page_parent')) {
      const parent = node.data.page_parent; offsets[parent] = node.data.next;
      tree.load_children(node.parent_node); return;
     }
     show(node.data.value);
    }});
   notice.text(__('Explora las ubicaciones o busca por nombre. Incluye ubicaciones desactivadas para conservar su historia.'));
  } catch (error) { if (request === sequence) notice.text(__('No se pudo cargar la jerarquía. Revisa la sede y tus permisos.')); }
 }
 async function applyOptions() {
  const route = frappe.route_options || {}; frappe.route_options = null;
  ready = false;
  if (route.company) await company.set_value(route.company);
  if (route.site) await site.set_value(route.site);
  ready = true; await load();
  if (route.location && site.get_value()) await show(route.location);
 }
 page.add_inner_button(__('Actualizar'), load);
 page.add_inner_button(__('Lista de ubicaciones'), () => list('VB Equipment Location', options()));
 page.add_inner_button(__('Nueva ubicación raíz'), async () => {
  if (!site.get_value()) { frappe.msgprint(__('Selecciona una sede.')); return; }
  if (!frappe.model.can_create('VB Equipment Location')) { frappe.msgprint(__('No tienes permiso para crear ubicaciones.')); return; }
  const {message} = await frappe.db.get_value('TruCMMS Site', site.get_value(), 'company');
  frappe.new_doc('VB Equipment Location', {site: site.get_value(), company: message.company});
 });
 wrapper.trucmms_locations = {applyOptions}; ready = true;
};
frappe.pages['trucmms-locations'].on_page_show = async function (wrapper) {
 if (!frappe.route_options && wrapper.trucmms_locations_initialized) return;
 const first = !wrapper.trucmms_locations_initialized;
 wrapper.trucmms_locations_initialized = true;
 if (!frappe.route_options && first) {
  const {message: sites} = await frappe.call({method: 'frappe.client.get_list', type: 'GET', args: {doctype: 'TruCMMS Site', fields: ['name', 'company'], limit_page_length: 2}});
  if (sites.length === 1) frappe.route_options = {site: sites[0].name, company: sites[0].company};
 }
 await wrapper.trucmms_locations.applyOptions();
};
