# Cuéntame

Una pequeña entrevistadora local para conservar recuerdos familiares sin pedirle a la IA que invente una biografía. Gemma, mediante Ollama en `127.0.0.1`, propone una pregunta a la vez. El archivo final copia **literalmente** las respuestas de la persona entrevistada. Los vacíos quedan abiertos.

Proyecto creado para [Hacktoberfest Open-Source AI Challenge: Week 4](https://dev.to/challenges/hacktoberfest-week4-2026-10-26), tema *Ghost in the Machine*. La demo ficticia y las pruebas de código no equivalen a una ejecución real del modelo.

## Uso

Requiere Python 3.10+ y [Ollama](https://ollama.com/). Descarga un modelo Gemma compatible con tu equipo y usa su nombre exacto con `--modelo`. El valor predeterminado es `gemma4:e2b`.

```sh
ollama pull gemma4:e2b
python3 cuentame.py --nombre "Elena" --modelo gemma4:e2b
```

Para ver solo el formato de salida, sin modelo:

```sh
python3 cuentame.py --ejemplo
```

Los resultados van a `recuerdos/`, excluido de Git. El programa no sobrescribe archivos existentes. El ejemplo usa una persona y respuestas ficticias. No subas entrevistas reales a un repositorio sin consentimiento.

## Comprobación

```sh
python3 -m unittest -v
```

Las pruebas simulan la respuesta HTTP de Ollama y comprueban la ruta local, el historial enviado y la copia literal de las respuestas. Falta una prueba de extremo a extremo con Gemma en ejecución.
