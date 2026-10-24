# TruCMMS

A custom Frappe application for an ERPNext-native CMMS. The current implementation is the equipment foundation: equipment, categories, locations, validation, maintenance roles and change history. Requests, work orders and preventive maintenance are subsequent increments.

## Architecture

Use Frappe documents, controllers, permissions and Desk. ERPNext owns enterprise masters and transactions. Maintenance Equipment remains distinct from financial Asset; maintenance locations are not automatically Warehouses. Do not modify Frappe or ERPNext business logic to implement this app.

The verified development baseline is Frappe 16.28.0, ERPNext 16.29.0, Python 3.14.7 and Node 24.21.0. Development and test sites must both contain Frappe, ERPNext and this app.

## Native ERPNext navigation

After installation or `bench --site SITE migrate`, reload ERPNext Desk and select **TruCMMS** from the desktop. Its workspace and sidebar open Equipment, Equipment Categories and Equipment Locations in the same Desk session. Visibility follows native maintenance-role permissions.

The current Python app identifier remains `vanbags_maintenance`, with existing `VB` DocTypes, roles and the internal `Vanbags Maintenance` module retained for compatibility. TruCMMS is the product name; VanBags is an optional example business. The technical package rename requires a separate migration and is not performed by this navigation increment.

## Equipment identity and labels

Equipment codes are manually entered at creation, normalized, unique and immutable afterwards. Desk uses native conditional read-only metadata; controllers enforce immutability on the server.

Category and location IDs are assigned from the initial trimmed label using Frappe expression naming. Their labels can subsequently change without changing IDs or equipment Links. Renaming document IDs is disabled; labels remain unique. An original ID stays reserved even after its label changes. Existing document names are preserved. Catalog edits and equipment edits retain Frappe Version history.

## Installation and testing

Install ERPNext on the target site before installing vanbags_maintenance:

```bash
bench --site SITE install-app erpnext
bench --site SITE install-app vanbags_maintenance
```

On the isolated test site:

```bash
bench --site test.vanbags.localhost run-tests --app vanbags_maintenance
```

The GitHub Actions definition installs pinned Frappe and ERPNext releases before running app tests. Remote CI execution must be verified separately from local checks.

The isolated Docker configuration and operational instructions are maintained in the Windows project at D:/Projects/VanBags-ERP/docker/development. The active app source is /home/vatru/vanbags-dev/frappe-bench/apps/vanbags_maintenance.

## License

MIT

## Company and site access

Equipment and functional locations now require Company and Site. Configure both native User Permissions for each maintenance user. Create operational sites as System Manager through TruCMMS → Sites. See [organization and access rules](docs/ORGANIZATION.md) for configuration, compatibility and tested boundaries.


## Maintenance requests

Native requests are documented in [Requests](docs/REQUESTS.md), including roles, organizational permissions, transitions and private evidence.
