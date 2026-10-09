# ORM con IA — duelo y verificador dentro de Nexo

Este es el laboratorio extra de la semana 7 de Desarrollo de Aplicaciones Empresariales, integrado desde `dae-s07-orm-con-ia`. El blog tiene autores, perfiles, artículos, categorías, etiquetas y comentarios para practicar ocho consultas del ORM de Django y verificar lo que produce una IA.

La guía docente y su rúbrica están en el campus virtual. Esta integración conserva la plantilla de ejercicios: no aporta soluciones ni incluye la carpeta privada `teacher/`.

## Preparación

Todos los comandos se ejecutan desde la raíz de Nexo, donde está `manage.py`. No hace falta iniciar el proyecto original ni instalar dependencias adicionales.

En PowerShell, con el entorno virtual preparado según el [README principal](../README.md):

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_blog
.\.venv\Scripts\python.exe manage.py runserver
```

Abre `http://127.0.0.1:8000/blog/`. La ruta mantiene el nombre `front_page` para que las pruebas originales sigan funcionando; solo cambia su dirección dentro del proyecto.

`seed_blog` carga siempre los mismos **4 autores, 15 artículos y 23 comentarios**. **Borra antes todos los datos del blog**, por lo que sirve para preparar o reiniciar el laboratorio, no para preservar publicaciones propias. No borra películas, noticias, usuarios ni permisos.

## Parte 1 — El duelo

Escribe tus ocho consultas en `blog/duel/team.py`, una función por pregunta. Devuelve un QuerySet o una lista según el contrato de `blog/duel/questions.py`; no escribas SQL ni filtres en Python lo que puede filtrar la base de datos.

| Función | Pregunta |
| --- | --- |
| `q1` | Artículos publicados. |
| `q2` | Artículos sin categoría. |
| `q3` | Artículos publicados entre el 1 de marzo y el 31 de mayo de 2026, ambos incluidos. |
| `q4` | Artículos con más de dos comentarios. |
| `q5` | Los tres artículos publicados con más comentarios, anotados con `n_comments` y `n_tags`. |
| `q6` | Artículos de autores de Perú, publicados o no. |
| `q7` | Comentarios de artículos de la categoría Tecnología. |
| `q8` | Autores que nunca han publicado un artículo. |

```powershell
.\.venv\Scripts\python.exe manage.py duel
.\.venv\Scripts\python.exe manage.py duel --question q4
.\.venv\Scripts\python.exe manage.py duel --source ai
```

Las respuestas de `ai_answers.py` son ejemplos guardados, no llamadas en directo a un modelo. Se mantienen sin corregir para que el duelo señale resultados correctos, correctos pero caros, distintos o con error. Las respuestas esperadas se calculan en Python a partir de los datos fijos, independientemente de las consultas.

Los indicadores de consola usan `[OK]`, `[!]` y `[X]` para evitar errores de codificación al redirigir la salida en Windows; esta adaptación no cambia las consultas ni los veredictos del laboratorio.

Para inspeccionar el SQL después de implementar una respuesta:

```powershell
.\.venv\Scripts\python.exe manage.py shell
```

```python
from blog.duel import team
print(team.q1().query)
```

## Parte 2 — Del rojo al verde

```powershell
.\.venv\Scripts\python.exe manage.py test blog.tests.test_front_page
```

La prueba `test_front_page_runs_two_queries` **falla a propósito**. La portada funciona, pero consulta el autor y las etiquetas de cada artículo por separado. Corrige únicamente la consulta de `blog/queries.py` hasta que la página se renderice con dos consultas.

La portada ahora hereda de `templates/base.html` y utiliza el navbar y el pie compartidos. Sigue recorriendo `post.author` y `post.tags.all`, por lo que el reto de rendimiento original permanece intacto.

## Parte 3 — La frontera

`blog/agent/registry.py` define una lista cerrada de acciones. No admite `eval`, SQL libre ni acceso genérico a la consola. Las lecturas se devuelven como `untrusted_data`; el texto de un comentario es información, no una instrucción que deba ejecutarse.

En PowerShell, `--%` evita que el shell altere las comillas del JSON enviado al comando:

```powershell
.\.venv\Scripts\python.exe --% manage.py agent --intent "{\"action\":\"posts_per_author\",\"args\":{}}"
.\.venv\Scripts\python.exe --% manage.py agent --intent "{\"action\":\"comments_of_post\",\"args\":{\"post_id\":1}}"
.\.venv\Scripts\python.exe --% manage.py agent --intent "{\"action\":\"delete_comments_of_post\",\"args\":{\"post_id\":1}}"
.\.venv\Scripts\python.exe --% manage.py agent --intent "{\"action\":\"run_sql\",\"args\":{}}"
```

La petición de borrado solo devuelve un plan y su hash; no aplica cambios sin aprobación humana del mismo plan mediante `--approve`. Una acción desconocida, como `run_sql`, se rechaza. La página pública no ejecuta estas acciones ni recibe aprobaciones.

Los datos iniciales incluyen deliberadamente un comentario que intenta dar órdenes a un modelo. Trátalo como texto de práctica, nunca como autorización.

### Adaptador opcional a un modelo local

Solo es necesario para usar `agent --ask`; el duelo, la portada y las pruebas no necesitan un modelo ni conexión externa.

```powershell
$env:LLM_URL = 'http://localhost:11434/v1'
$env:LLM_MODEL = 'qwen2.5:7b'
.\.venv\Scripts\python.exe manage.py agent --ask "¿cuántos artículos tiene cada autor?"
```

Usa un endpoint compatible con OpenAI y un modelo instalado en tu servidor local. El modelo propone una intención, pero la pasarela decide si se admite. `--ask` nunca aplica una aprobación proporcionada al comando.

## Pruebas y estructura

```powershell
.\.venv\Scripts\python.exe manage.py test blog --verbosity 2
```

Hay 24 pruebas originales y 7 de integración con Nexo. En la plantilla inicial debe fallar únicamente el ejercicio N+1; dos pruebas de referencia se omiten al no estar disponible `teacher/`. La prueba `test_the_starter_has_nothing_written` comprueba el estado inicial de las ocho respuestas: cuando las implementes, actualiza esa comprobación para validar tus respuestas en lugar de esperar que estén pendientes.

| Ruta | Función |
| --- | --- |
| `blog/models.py` | `Author`, `Profile`, `Category`, `Tag`, `Post`, `Comment`. |
| `blog/seed_data.py` | Datos fijos y comentario de práctica. |
| `blog/duel/team.py` | Tus ocho respuestas. |
| `blog/duel/ai_answers.py` | Respuestas guardadas de la IA. |
| `blog/duel/questions.py` | Contratos, respuestas esperadas y presupuestos de consultas. |
| `blog/queries.py` | Consulta de la portada, pendiente de optimizar. |
| `blog/agent/` | Pasarela de acciones y adaptador opcional al modelo. |
| `blog/tests/test_integration.py` | Rutas, navegación, administrador y separación de datos. |

Convenciones del curso: código, nombres y comentarios en inglés; explicaciones y entregables en español; PEP 8.
