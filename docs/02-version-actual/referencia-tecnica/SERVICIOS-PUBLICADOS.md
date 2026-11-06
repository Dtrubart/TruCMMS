# Servicios publicados de la revisión verificada

Fuente: `fbca17e584159990bd16a2853228242b2f2454fa`.
Registro extraído de decoradores frappe.whitelist sin ejecutar código. No sustituye controles de rol, estado, alcance ni contratos detallados. Las firmas son Python; serialización/valores API siguen Frappe.

## vanbags_maintenance.adjustments

- `vanbags_maintenance.adjustments.void_entry(execution, reason)` — ['POST']

## vanbags_maintenance.allocations

- `vanbags_maintenance.allocations.add(work_order, technician, discipline, reason)` — ['POST']
- `vanbags_maintenance.allocations.remove(allocation, reason)` — ['POST']
- `vanbags_maintenance.allocations.mine(work_order)` — según configuración Frappe

## vanbags_maintenance.assets

- `vanbags_maintenance.assets.adopt(equipment, reason)` — ['POST']
- `vanbags_maintenance.assets.place(equipment, site, location=None, reason=None, effective_on=None)` — ['POST']
- `vanbags_maintenance.assets.remove(equipment, reason, effective_on=None)` — ['POST']
- `vanbags_maintenance.assets.replace(equipment, replacement, reason, effective_on=None)` — ['POST']
- `vanbags_maintenance.assets.configure(equipment, reason, asset_tag=None, technical_profile=None, values=None, criticality=None)` — ['POST']
- `vanbags_maintenance.assets.configure_position(location, single_equipment, reason)` — ['POST']

## vanbags_maintenance.capacity

- `vanbags_maintenance.capacity.overview(company, site, technician, from_date, to_date)` — ['GET']

## vanbags_maintenance.components

- `vanbags_maintenance.components.place(component, equipment=None, position=None, reason=None, effective_on=None)` — ['POST']
- `vanbags_maintenance.components.history(component)` — ['GET', 'POST']

## vanbags_maintenance.configuration

- `vanbags_maintenance.configuration.operating_clock(site, value=None)` — según configuración Frappe

## vanbags_maintenance.fulfillment

- `vanbags_maintenance.fulfillment.delivery(request, key)` — ['POST']
- `vanbags_maintenance.fulfillment.return_draft(issue, key)` — ['POST']
- `vanbags_maintenance.fulfillment.acknowledge(stock_entry, reason)` — ['POST']
- `vanbags_maintenance.fulfillment.reconciliation(order)` — ['GET']

## vanbags_maintenance.inspections

- `vanbags_maintenance.inspections.report(execution, description, key, component=None)` — ['POST']
- `vanbags_maintenance.inspections.review(finding, disposition, reason)` — ['POST']
- `vanbags_maintenance.inspections.followup(finding, reason, priority='Medium')` — ['POST']

## vanbags_maintenance.job_plans

- `vanbags_maintenance.job_plans.approve(name, approval_reason)` — ['POST']
- `vanbags_maintenance.job_plans.retire(name, retirement_reason)` — ['POST']
- `vanbags_maintenance.job_plans.revise(name, change_reason)` — ['POST']
- `vanbags_maintenance.job_plans.approved_snapshot(name)` — ['GET', 'POST']

## vanbags_maintenance.lifecycle

- `vanbags_maintenance.lifecycle.perform(work_order, action, reason)` — ['POST']

## vanbags_maintenance.logistics

- `vanbags_maintenance.logistics.context(order)` — ['GET']
- `vanbags_maintenance.logistics.item_choices(order, search='', kind='All', limit=20)` — ['GET']

## vanbags_maintenance.materials

- `vanbags_maintenance.materials.forecast(company, site, from_date, to_date)` — ['GET']
- `vanbags_maintenance.materials.purchase_request(company, site, from_date, to_date, warehouse, keys, key, reason)` — ['POST']
- `vanbags_maintenance.materials.issue_request(order, warehouse, items, key, reason)` — ['POST']

## vanbags_maintenance.meters

- `vanbags_maintenance.meters.record(meter_name, value, actual_on, key, reason=None)` — ['POST']
- `vanbags_maintenance.meters.correct(reading, value, reason, key)` — ['POST']
- `vanbags_maintenance.meters.reset(meter_name, initial_value, reason, key, actual_on=None)` — ['POST']
- `vanbags_maintenance.meters.readings(meter_name)` — ['GET', 'POST']

## vanbags_maintenance.navigation

- `vanbags_maintenance.navigation.home(company=None, site=None)` — ['GET', 'POST']

## vanbags_maintenance.preventive

- `vanbags_maintenance.preventive.preview(plan, from_date=None, to_date=None)` — ['GET', 'POST']
- `vanbags_maintenance.preventive.materialize(plan, until=None)` — ['POST']
- `vanbags_maintenance.preventive.activate(plan, reason, baseline_reading=None)` — ['POST']
- `vanbags_maintenance.preventive.disposition(plan, action, reason)` — ['POST']
- `vanbags_maintenance.preventive.rebase(plan, reading, reason)` — ['POST']
- `vanbags_maintenance.preventive.renew_condition(plan, reason)` — ['POST']
- `vanbags_maintenance.preventive.release(occurrence_name, reason, override=0)` — ['POST']
- `vanbags_maintenance.preventive.change_occurrence(occurrence_name, action, reason, planned_for=None)` — ['POST']
- `vanbags_maintenance.preventive.start_work(work_order, reason)` — ['POST']
- `vanbags_maintenance.preventive.run_plan(plan, reason)` — ['POST']
- `vanbags_maintenance.preventive.schedule(from_date, to_date, company=None, site=None, equipment=None, plan=None)` — ['GET', 'POST']
- `vanbags_maintenance.preventive.compliance(from_date, to_date, company=None, site=None, equipment=None, plan=None)` — ['GET', 'POST']

## vanbags_maintenance.resource_calendars

- `vanbags_maintenance.resource_calendars.generate(assignment, from_date, to_date, reason)` — ['POST']

## vanbags_maintenance.resource_costs

- `vanbags_maintenance.resource_costs.summary(order)` — ['GET']

## vanbags_maintenance.resource_planning

- `vanbags_maintenance.resource_planning.availability(company, site, from_date, to_date, warehouse)` — ['GET']
- `vanbags_maintenance.resource_planning.shopping_csv(company, site, from_date, to_date)` — ['GET']

## vanbags_maintenance.submission

- `vanbags_maintenance.submission.submit(payload, key)` — ['POST']

## vanbags_maintenance.teams

- `vanbags_maintenance.teams.adopt_legacy(work_order, team, discipline, reason)` — ['POST']

## vanbags_maintenance.work_contract

- `vanbags_maintenance.work_contract.create_direct(company, site, subject, scope, priority, key, reason, equipment=None, functional_location=None, acceptance_user=None)` — ['POST']

## vanbags_maintenance.work_cycle

- `vanbags_maintenance.work_cycle.perform(work_order, action, reason)` — ['POST']
- `vanbags_maintenance.work_cycle.replan(work_order, scheduled_start=None, scheduled_end=None, target_closure=None, reason=None)` — ['POST']
- `vanbags_maintenance.work_cycle.reassign(work_order, technician, reason, team=None, discipline=None)` — ['POST']
- `vanbags_maintenance.work_cycle.adopt(work_order, reason, acceptance_user=None)` — ['POST']
- `vanbags_maintenance.work_cycle.designate_acceptor(work_order, user, reason)` — ['POST']

## vanbags_maintenance.work_orders

- `vanbags_maintenance.work_orders.from_request(request)` — ['POST']

## vanbags_maintenance.work_scope

- `vanbags_maintenance.work_scope.configure(order, scope_location, targets, reason, key)` — ['POST']
- `vanbags_maintenance.work_scope.record_reading(order, target_id, meter, value, actual_on, key, reason)` — ['POST']
- `vanbags_maintenance.work_scope.overview(order)` — ['GET']

## vanbags_maintenance.work_views

- `vanbags_maintenance.work_views.get_work(filters=None)` — ['GET', 'POST']
- `vanbags_maintenance.work_views.execution_order_query(doctype, txt, searchfield, start, page_len, filters=None)` — según configuración Frappe

## Ampliacion local ENT-002 — vanbags_maintenance.location_hierarchy

Inventario actual de trabajo: 70 servicios publicados.

- `children(site, parent=None, start=0, search=None, company=None)` — GET; consulta autorizada, paginas de 50.
- `details(name)` — GET; ficha, ruta e historial acotado.
- `preview(name, action, parent=None)` — POST; escritura requerida, devuelve impacto y token.
- `change(name, action, token, reason, parent=None)` — POST; revalida token/alcance, cambio atomico e historial.

Acciones: Reparent, Deactivate, Reactivate. El token detecta obsolescencia; no es una credencial y no reemplaza permisos. No admite fecha efectiva enviada por cliente.
