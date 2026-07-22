# Threat intel — cuotas y modo live

SecOps Hub enriquece IOCs con **AbuseIPDB** y **VirusTotal** cuando hay API keys.
Sin claves, el enriquecimiento es **simulado** (determinista) y el campo `enrichment_mode`
indica `simulated`.

## Variables

```env
ABUSEIPDB_API_KEY=...
VIRUSTOTAL_API_KEY=...
```

Estado: `GET /api/integrations/status` → `triaje.mode` = `live` | `simulated`.

## Cuotas típicas (revisar plan vigente)

| Proveedor | Plan free (orientativo) | Notas |
|-----------|-------------------------|--------|
| AbuseIPDB | ~1.000 checks / día | Header `Key`; endpoint `/api/v2/check` |
| VirusTotal | ~500 requests / día, ~4 req/min | Header `x-apikey`; API v3 |

Los planes de pago aumentan el cupo. Si se agota la cuota, SecOps Hub hace **fallback
automático a simulado** y registra el motivo en la respuesta de enriquecimiento.

## Buenas prácticas

1. No commitear claves; usar `.env` o secretos del orquestador.
2. Preferir enriquecimiento bajo demanda (triaje) frente a barridos masivos.
3. Cachear resultados en BD (IOC ya enriquecido) antes de volver a llamar a la API.
4. Monitorizar errores 429 en logs (`secops.http` / clientes externos).

## Prueba rápida

```bash
curl -X POST http://localhost:5000/api/iocs/enrich \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"value":"8.8.8.8"}'
```
