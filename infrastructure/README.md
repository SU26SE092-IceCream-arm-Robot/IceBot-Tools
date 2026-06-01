# Local Infrastructure Notes

This folder contains public-safe templates for local machine and tooling runtime notes.

These files are not project architecture truth. They help a developer document their own local setup when running RAG, Docker services, scripts, or other tooling.

## How To Use

Copy the templates into `IceBot-Tools/.local/` and fill in local details there:

```text
IceBot-Tools/.local/MACHINE_PROFILE.md
IceBot-Tools/.local/RAG_RUNTIME_OBSERVATIONS.md
```

`IceBot-Tools/.local/` is ignored by git and can contain machine-specific paths, hardware details, and local observations.

## Public Files

- `MACHINE_PROFILE.example.md`: safe template for local hardware/runtime profile.
- `RAG_RUNTIME_OBSERVATIONS.example.md`: safe template for local RAG performance observations.

## Rules

- Do not store secrets in either templates or local files.
- Do not commit real machine fingerprints unless intentionally public.
- Do not treat local machine notes as project source of truth.
- Keep operational RAG commands in `IceBot-Tools/rag`.
- Keep project decisions and trade-offs in `Vault`.
