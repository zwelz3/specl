# EKGA Spec - Deferred Features (tracked for future iterations)

## Traceability and linking (deferred from iteration N)
Need first-class support for binding spec entries to the running system:
- **Component registry** (`ekga:Component` individuals) so `ekga:constrains` links resolve to real artifacts, with a validator for dangling refs.
- **Test registry** (`ekga:Test` individuals) so `ekga:verifiedBy` links resolve, ideally auto-populated by a pytest collector.
- **Live binding**: deployed app exposes its spec IRI + version at a known endpoint so agents can ask "what requirement governs this endpoint?"
- Priority: SHOULD. Blocks production-grade traceability but not prototype work.

## Domain extension pattern (deferred from iteration N)
`ekga-core.ttl` ships as a minimal OWL stub. Still needed:
- **DomainExtension import pattern**: a documented convention for per-deployment ontologies that `owl:imports` ekga-core and adds business classes.
- **Worked example**: one concrete DomainExtension (e.g., for C2 logistics) showing the pattern end-to-end.
- Priority: SHOULD. Required before first real deployment.
