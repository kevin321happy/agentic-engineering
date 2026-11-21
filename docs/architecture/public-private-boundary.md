# Public and private boundary

The public repository contains provider-neutral protocol models, runtime interfaces, generic workflows, fake adapters, synthetic fixtures, replay tests, and documentation.

A private enterprise pack contains project profiles, business source code references, internal issue-tracker and CI adapters, credentials, private RAG indexes, historical incident details, real API payloads, real accounts, device assets, and organization-specific approval rules.

The public core must not import or require an enterprise pack. Enterprise integrations implement public adapter contracts and inject project-specific policy through configuration. RAG results are advisory context and cannot satisfy proof requirements or approve a gate by themselves.

A secret or private business artifact is considered exposed once committed to a public repository; deleting it later does not remove it from Git history or caches.
