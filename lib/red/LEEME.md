# lib/red: red y HTTP para programas Dash

Vienen de Tachyon (sus `lib/*.dash` de la rama `dash2`, ya sin C). Se importan desde cualquier carpeta:
`import "lib/red/http.dash"` (dashc y dash1 buscan también en la carpeta de Dash; `$DASH_HOME` la cambia).

| Fichero | Qué hace |
|---------|----------|
| `red.dash` | Conexiones TCP y TLS (AmiSSL) en una tarea aparte, con los builtins `net_bg_*` |
| `http.dash` | Cliente HTTP/1.1 y HTTPS: GET, POST, cualquier método con cabeceras propias, con espera o sin ella |
| `url.dash` | Analizar, resolver y escribir URL |
| `cookies.dash` | Las cookies que manda y recibe `http.dash` |
| `traza.dash`, `idioma.dash` | La traza de tiempos (`traza_activa`) y `hueco`/`hueco2` para los textos de `tr()` |

Una API que espera JSON, con `lib/json.dash`:

```dash
import "lib/red/http.dash"
import "lib/json.dash"

r = http_pedir("https://openrouter.ai/api/v1/chat/completions", "POST", json_write(peticion),
               "application/json", "Authorization: Bearer " + clave, 60000)
if r.error == ""
    texto = json_path_str(json_parse(r.cuerpo), "choices.0.message.content")
end
```

Una respuesta que se lee según llega (`"stream": true`, eventos SSE), sin compresión:

```dash
c = http_empezar_flujo(url, "POST", json_write(peticion), "application/json", "Authorization: Bearer " + clave, 300000)
while not http_avanzar(c)
    nuevo = http_flujo_leer(c)            # lo nuevo del cuerpo, sin el marco de chunked; "" si no hay
end
nuevo = http_flujo_leer(c)                # lo último; c.respuesta queda entera (un 4xx con su JSON)
```

Los errores de red van con `tr()` y los números 400 a 442: un programa con catálogo no debe usar esos números.

## Diferencias con los de Tachyon

Lo que es solo del navegador se quedó fuera:

- `http.dash`: el User-Agent es la variable `http_agente` ("Dash (AmigaOS)"; antes, la constante `HTTP_AGENTE`).
  `http_texto` pasa a Latin-1 solo un cuerpo en UTF-8, con `utf8_to_latin1` (el de Tachyon usaba
  `texto_decodificar` de su `texto.dash`). Nuevas: `http_pedir`, cualquier método esperando a la respuesta, y `http_empezar_flujo` con `http_flujo_leer`.
- `url.dash`: sin `url_fuentes_latin1` (Google Fonts) ni `url_rastreador` y sus constantes.
- `cookies.dash`: sin `cookies_html` (la página `tachyon:cookies`).

Para que Tachyon importe estos (pendiente, con su sesión): quitar sus `red`, `http`, `url`, `cookies`, `traza` e
`idioma`, importar los de aquí, poner `http_agente = "Tachyon/..."` al arrancar y llevar a un módulo suyo lo que se
quedó fuera (su `http_texto` con otro nombre, `url_rastreador`, `url_fuentes_latin1`, `cookies_html`).
