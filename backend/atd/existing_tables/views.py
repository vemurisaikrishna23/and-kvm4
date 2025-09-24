from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Users


@csrf_exempt
def create_user(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON body'}, status=400)

    required_fields = ['name', 'mobile', 'password']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return JsonResponse({'detail': 'Missing required fields', 'fields': missing}, status=400)

    # Optional fields
    email = data.get('email')
    country_code = data.get('country_code')
    alternate_mobile = data.get('alternate_mobile')
    company_name = data.get('company_name')
    image = data.get('image')
    organization_id = data.get('organization_id')

    try:
        user = Users.objects.create(
            name=data['name'],
            email=email,
            country_code=country_code,
            mobile=data['mobile'],
            alternate_mobile=alternate_mobile,
            password=data['password'],
            organization_id=organization_id,
            company_name=company_name,
            image=image,
        )
    except Exception as exc:
        return JsonResponse({'detail': 'Could not create user', 'error': str(exc)}, status=400)

    return JsonResponse({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'mobile': user.mobile,
    }, status=201)
