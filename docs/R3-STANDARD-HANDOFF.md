# R3 — standard maintenance/logistics handoff

This increment uses native ERPNext catalogs and Material Requests. It does not introduce a separate maintenance inventory, bypass native approval workflows, grant stock/purchase roles, or post physical/financial transactions automatically.

## Delivered contract

- `TruCMMS Site Warehouse`: immutable Company/Site/Warehouse binding, disabled rather than deleted; supervisor configuration plus native Warehouse read permission. Mapping and native Warehouse permissions both restrict choices.
- **Repuestos y costos → Proyección de materiales**: Company/Site/date-bounded projection of the frozen material estimates on active preventive occurrences. Released occurrences use the linked order snapshot and remain the same demand, not a second source. Closed/cancelled work and skipped/cancelled occurrences are excluded; paused plans do not create future demand in this report.
- The projection shows stock UOM, gross planned quantities, quantities on live purchase requests, and requirements not yet handed off. It is **not net stock availability, a reservation or an automatic replenishment recommendation**. Warehouse/procurement reviews availability and quantities before approving a purchase.
- A reviewed selection creates a native **Material Request / Purchase / Draft**. Items with the same stock UOM are consolidated into a single native item line, using the earliest required date. The read-only TruCMMS demand detail retains each occurrence, original quantity, required date and stable source identity. This works with native duplicate-item prohibition enabled. Repeating the same request key returns the same document; another request cannot duplicate active source lines. Cancelled requests retain historical references and release their source keys for a new handoff.
- Authorized/Assigned work orders can create a native **Material Request / Material Issue / Draft** from entered stock materials, with procedure quantities prefilled when available. The request is linked to the work order. Assigned technicians additionally require native Material Request create/read and Warehouse/Item access. Requesters and unassigned technicians cannot bypass those gates.
- Existing native procurement workflows continue from the draft. Material issue drafts do not deduct stock. Actual fulfillment remains in native warehouse transactions. Native linked Stock Entries must respect the maintenance request Company/Site and authorized warehouses.
- Native requests without a TruCMMS origin retain native behavior and visibility. TruCMMS requests require explicit Company/Site scope; document sharing cannot expand this access. Frozen origin fields cannot be forged through normal document/API writes.

## R3 completion: native fulfillment, estimates and costs

The projection covers frozen preventive snapshots and explicit additional Material Estimates for open direct/corrective work orders. Estimates on preventive orders are supplementary, never replacements for frozen procedure requirements. Handed-off estimates retain their source identity and quantities.

The interface currently sends all unrequested lines in the displayed projection; the API also supports a selected subset. Buyers may review native draft quantities; the report allocates the consolidated quantity proportionally across its demand sources. Source details cannot be inserted, changed or deleted directly through child document operations. Normal parent saves and draft deletion remain supported. Existing requests remain visibly linked rather than automatically generating extra requests when a buyer adjusts a quantity.

After cancellation, regenerate the request from the forecast/work order. Native amendment of a TruCMMS request is blocked until provenance-preserving amendment support is implemented; ordinary ERPNext requests are unaffected.

- A submitted native issue request can prepare a native Stock Entry / Material Issue draft. Native save/submit permissions and workflows remain authoritative. Partial delivery is supported; competing submissions cannot exceed the requested quantity.
- The assigned technician or scoped supervisor confirms collection of a submitted issue using their authenticated account. The immutable acknowledgment stores receiver, server timestamp, reason and material snapshot. A printable collection receipt is provided. This is account-based confirmation, not an external electronic-signature integration.
- Returns are native Material Receipt drafts tied to the original issue and detail. Partial quantities, original serials/batches and valuation are validated; submitted returns cannot exceed the issued units. Cancellation requires reversing submitted returns first. Acknowledgments survive as historical evidence when an issue is cancelled.
- Work order reconciliation separates requested, issued, returned and net issued quantities. Draft/cancelled stock movements do not count. Net issued is an inventory-based measure, not a separate measurement of physical consumption.
- Native non-stock Purchase Invoice lines and Employee Timesheet lines can reference the maintenance order. Credit notes preserve references. Cost summaries use native stock valuation, invoice net amounts and timesheet costing in Company currency; taxes, forecasts and payment status are excluded. Missing native permissions produce an explicitly incomplete total, never a misleading zero.
- The advisory availability view uses current native stock less native reserved_stock, then compares it with unrequested forecast demand. It does not allocate future supply, reserve stock or automatically reduce purchase drafts; procurement reviews the suggestion.
- A controlled CSV shopping list supports external purchasing. Goods received outside the procurement workflow are entered using the normal native Material Receipt form, with the required warehouse, quantity, valuation and serial/batch data. No parallel inventory is introduced.

## Acceptance boundary

Technical verification, populated recovery, concurrent request handling and browser evidence are recorded separately with their exact revision in the project implementation report. Human acceptance and production deployment remain separate from technical completion. Advanced resource optimization belongs to R4; prediction/reliability to R5; offline mobile to R6.

No new synthetic users, warehouse authorizations, purchases, stock balances or demo logistics transactions are installed by app migration. Existing maintenance users are not silently assigned Stock User/Purchase User roles. Configure legitimate logistics users and Site/Warehouse authorizations explicitly.
