# SecureHRM Flask demo

Denne applikation er lavet som en **bevidst sårbar** undervisningsapp til session 11 om sikkerhedstest og sikker fejlhåndtering.

## Vigtigt

Kør den **kun lokalt** i et kontrolleret testmiljø. Den må ikke deployes offentligt.

## Dækkede sårbarheder

- SQL Injection: `/reports`
- XSS: `/feedback`
- Insecure File Upload: `/upload`
- Command Injection: `/backup`
- Path Traversal: `/download?filename=...`
- Verbose error handling: `/crash`

## Start applikationen

```bash
cd securehrm_flask
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Appen starter som udgangspunkt på:

```text
http://127.0.0.1:5000
```

## Nulstil demo-data

Åbn:

```text
http://127.0.0.1:5000/init
```

## Forslag til sikre testpayloads

Brug kun ufarlige payloads i undervisningen.

- SQLi: prøv klassiske filter-bypass inputs, der kun læser data
- XSS: simple `alert()`-tests
- Command injection: brug fx ekstra `echo`-kommandoer i stedet for destruktive kommandoer
- Path traversal: prøv at læse lokale tekstfiler i projektmappen

## Didaktisk note

Appen matcher casens fokusområder og giver de studerende noget konkret at teste imod, samtidig med at de kan arbejde med remediation-forslag bagefter.


## Kør med Docker

Byg og start containeren:

```bash
docker compose up --build
```

Appen er derefter tilgængelig på:

```text
http://127.0.0.1:5000
```

Stop igen med:

```bash
docker compose down
```

Uploads og backupfiler mountes som volumes, så de bevares mellem genstarter.
