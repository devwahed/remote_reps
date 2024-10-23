from drf_yasg.utils import swagger_auto_schema
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Brand


class BrandProductsView(APIView):
    """
    List all brands with their products.
    """
    renderer_classes = [JSONRenderer]  # Ensure the view returns JSON format only

    @swagger_auto_schema(
        operation_description="Retrieve a list of all brands with their related products.",
        responses={200: 'A list of brands with products'}
    )
    def get(self, request):
        # Fetch all brands and their related products
        brands = Brand.objects.prefetch_related('products').all()

        # Create a list of brands with their products
        brand_list = [
            {
                "name": brand.name,
                "products": [{"id": product.id, "name": product.name} for product in brand.products.all()]
            } for brand in brands
        ]

        return Response(brand_list)
