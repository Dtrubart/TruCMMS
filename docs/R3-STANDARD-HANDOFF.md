# R3 — standard maintenance/logistics handoff

This increment uses native ERPNext catalogs and Material Requests. It does not introduce a separate maintenance inventory, bypass native approval workflows, grant stock/purchase roles, or post physical/financial transactions automatically.

## Delivered contract

- `TruCMMS Site Warehouse`: immutable Company/Site/Warehouse binding, disabled rather than deleted; supervisor configuration plus native Warehouse read permission. Mapping and native Warehouse permissions both restrict choices.
- **Repuestos y costos → Proyección de materiales**: Company/Site/date-bounded projection of the frozen material estimates on active preventive occurrences. Released occurrences use the linked order snapshot and remain the same demand, not a second source. Closed/cancelled work and skipped/cancelled occurrences are excluded; paused plans do not create future demand in this report.
- The projection shows stock UOM, gross planned quantities, quantities on live purchase requests, and requirements not yet handed off. It is **not net stock availability, a reservation or an automatic replenishment recommendation**. Warehouse/procurement reviews availability and quantities before approving a purchase.
- A reviewed selection creates a native **Material Request / Purchase / Draft**. Every forecast line retains its occurrence and stable source identity. Repeating the same request key returns the same document; another request cannot duplicate active source lines. Cancelled requests retain historical references and release their source keys for a new handoff.
- Authorized/Assigned work orders can create a native **Material Request / Material Issue / Draft** from entered stock materials, with procedure quantities prefilled when available. The request is linked to the work order. Assigned technicians additionally require native Material Request create/read and Warehouse/Item access. Requesters and unassigned technicians cannot bypass those gates.
- Existing native procurement workflows continue from the draft. Material issue drafts do not deduct stock. Actual fulfillment remains in native warehouse transactions. Native linked Stock Entries must respect the maintenance request Company/Site and authorized warehouses.
- Native requests without a TruCMMS origin retain native behavior and visibility. TruCMMS requests require explicit Company/Site scope; document sharing cannot expand this access. Frozen origin fields cannot be forged through normal document/API writes.

## Limits of this first R3 delivery

The projection currently covers material estimates in R2 preventive snapshots, not manual estimates for every direct/corrective work order. Issue requests can nevertheless be entered for authorized direct/corrective work.

The interface currently sends all unrequested lines in the displayed projection; the API also supports a selected subset. Buyers may review native draft quantities. Existing requests remain visibly linked rather than automatically generating extra requests when a buyer adjusts a quantity.

After cancellation, regenerate the request from the forecast/work order. Native amendment of a TruCMMS request is blocked until provenance-preserving amendment support is implemented; ordinary ERPNext requests are unaffected.

Still pending within the approved R3 roadmap: stock-aware net purchase proposals, export templates/external-purchase receipt scenarios, dedicated collection acknowledgment/signature and vale reconciliation, material returns/consumption summaries/cost reconciliation, and the final representative logistics pilot with candidate recovery. Native procurement and fulfillment documents are available, but those end-to-end R3 experiences are not certified complete by this increment.

No new synthetic users, warehouse authorizations, purchases, stock balances or demo logistics transactions are installed by app migration. Existing maintenance users are not silently assigned Stock User/Purchase User roles. Configure legitimate logistics users and Site/Warehouse authorizations explicitly.
