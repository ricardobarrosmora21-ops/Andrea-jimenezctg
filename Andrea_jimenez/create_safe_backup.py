import json

try:
    with open('backup_render.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    safe_models = [
        'auth.user',
        'configuraciones.categoria',
        'configuraciones.prenda',
        'configuraciones.imagenprenda',
        'configuraciones.cliente',
    ]

    filtered = []
    for item in data:
        if item['model'] in safe_models:
            # Eliminar referencias a grupos y permisos que rompen loaddata
            if item['model'] == 'auth.user':
                item['fields']['groups'] = []
                item['fields']['user_permissions'] = []
            filtered.append(item)

    with open('safe_backup.json', 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2)
    print("Safe backup generated!")
except Exception as e:
    print(f"Error: {e}")
