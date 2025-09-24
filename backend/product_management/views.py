from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
import logging

from .models import (
    Banner, Category, Tag, Brand, ProductAttribute, AttributeValue, 
    Product, ProductVariation, Review, ProductImage
)
from .serializers import (
    BannerSerializer, CategorySerializer, TagSerializer, BrandSerializer, ProductAttributeSerializer, 
    AttributeValueSerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductVariationSerializer, ReviewSerializer,
    ProductImageSerializer
)

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'description', 'meta_title']
    ordering_fields = ['name', 'created_at']
    ordering = ['name', 'created_at']

    def get_queryset(self):
        """
        Optionally filter by active status for non-staff users
        """
        queryset = Category.objects.all()        
        return queryset

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Support both single and bulk creation of categories
        """
        # Check if the data is a list for bulk creation
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': f'Successfully created {len(serializer.data)} categories',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Handle single object creation
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': 'Category created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def parent_categories(self, request):
        """Get only parent categories (no parent)"""
        try:
            queryset = self.get_queryset()
            parent_categories = queryset.filter(parent__isnull=True).order_by('name')
            serializer = self.get_serializer(parent_categories, many=True)
            return Response({
                'success': True,
                'categories': serializer.data,
                'count': parent_categories.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving parent categories: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve parent categories',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def with_images(self, request):
        """Get categories that have images"""
        try:
            queryset = self.get_queryset()
            categories_with_images = queryset.exclude(
                image__exact='', image_url__exact=''
            ).filter(
                Q(image__isnull=False) | Q(image_url__isnull=False)
            ).order_by('name')
            
            serializer = self.get_serializer(categories_with_images, many=True)
            return Response({
                'success': True,
                'categories': serializer.data,
                'count': categories_with_images.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving categories with images: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve categories with images',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products for a specific category"""
        try:
            category = self.get_object()
            
            # Get products for this category
            products = category.products.filter(is_active=True)
            
            # Apply pagination
            page = self.paginate_queryset(products)
            if page is not None:
                from .serializers import ProductListSerializer
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'category': CategorySerializer(category).data,
                    'products': serializer.data
                })
            
            from .serializers import ProductListSerializer
            serializer = ProductListSerializer(products, many=True)
            return Response({
                'success': True,
                'category': CategorySerializer(category).data,
                'products': serializer.data,
                'count': products.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving category products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve category products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Support both single and bulk creation of tags
        """
        # Check if the data is a list for bulk creation
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': f'Successfully created {len(serializer.data)} tags',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Handle single object creation
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': 'Tag created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Support both single and bulk creation of brands
        """
        # Check if the data is a list for bulk creation
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': f'Successfully created {len(serializer.data)} brands',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Handle single object creation
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'success': True,
                    'message': 'Brand created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)


class ProductAttributeViewSet(viewsets.ModelViewSet):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]


class AttributeValueViewSet(viewsets.ModelViewSet):
    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['attribute']
    search_fields = ['value', 'attribute__name']
    ordering_fields = ['attribute__name', 'value', 'created_at']
    ordering = ['attribute__name', 'value']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['brand', 'product_type', 'is_active', 'tags']
    search_fields = ['name', 'brand__name', 'description', 'sku']
    ordering_fields = ['name', 'brand__name', 'price', 'rating', 'created_at', 'product_views', 'quantity_sold']
    ordering = ['-created_at']

    def get_all_subcategories(self, category):
        """Recursively get all subcategories including the category itself"""
        subcategories = [category.id]
        for subcategory in category.subcategories.all():
            subcategories.extend(self.get_all_subcategories(subcategory))
        return subcategories

    def get_queryset(self):
        """
        Optionally restricts the returned products based on user permissions
        and handles category filtering with subcategories
        """
        queryset = Product.objects.select_related('category', 'brand').prefetch_related(
            'tags', 
            'reviews',
            'variations__attribute_values__attribute',
            'variations__attribute_values',
            'variations__productvariationvalue_set__attribute_value__attribute'
        )
        
        if self.request.user.is_staff:
            # Staff can see all products including inactive ones
            queryset = queryset
        else:
            # Regular users only see active products
            queryset = queryset.filter(is_active=True)
        
        # Handle category filtering with subcategories
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                from .models import Category
                category = Category.objects.get(id=category_id)
                
                # Get all descendant categories (subcategories at all levels)
                category_ids = self.get_all_subcategories(category)
                
                # Filter products by the category and all its subcategories
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                # If category doesn't exist, return empty queryset
                queryset = queryset.none()
        
        return queryset

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        else:
            return ProductDetailSerializer

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve', 'featured', 'best_sellers', 'new_arrivals', 'pocket_friendly', 'high_end', 'by_brand', 'by_category', 'search', 'price_range', 'product_collections', 'samsung_products', 'infinix_products']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """Override list method"""
        # Get the queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # No pagination
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to increment product views
        """
        try:
            instance = self.get_object()
            instance.increment_views()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'product': serializer.data
            })
        except Exception as e:
            logger.error(f"Error retrieving product: {str(e)}")
            return Response({
                'success': False,
                'message': 'Product not found',
                'errors': {'detail': ['Product does not exist']}
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products (highest rated or most viewed)"""
        try:
            featured_products = self.get_queryset().filter(
                rating__gte=4.0
            ).order_by('-rating', '-product_views')[:10]
            
            serializer = ProductListSerializer(featured_products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': featured_products.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving featured products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve featured products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        """Get best selling products"""
        try:
            best_sellers = self.get_queryset().filter(
                quantity_sold__gt=0
            ).order_by('-quantity_sold')[:10]
            
            serializer = ProductListSerializer(best_sellers, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': best_sellers.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving best sellers: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve best sellers',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """Get newest products"""
        try:
            new_arrivals = self.get_queryset().order_by('-created_at')[:10]
            
            serializer = ProductListSerializer(new_arrivals, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': new_arrivals.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving new arrivals: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve new arrivals',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def variations(self, request, pk=None):
        """Get variations for a specific product"""
        try:
            product = self.get_object()
            variations = product.variations.all()
            serializer = ProductVariationSerializer(variations, many=True)
            return Response({
                'success': True,
                'variations': serializer.data,
                'count': variations.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving product variations: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve product variations',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def pocket_friendly(self, request):
        """Get cheapest products (pocket-friendly)"""
        try:
            # Get products ordered by price ascending (cheapest first)
            pocket_friendly = self.get_queryset().order_by('price')[:10]
            
            serializer = ProductListSerializer(pocket_friendly, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': pocket_friendly.count(),
                'message': 'Pocket-friendly products retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error retrieving pocket-friendly products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve pocket-friendly products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def high_end(self, request):
        """Get most expensive products (high-end)"""
        try:
            # Get products ordered by price descending (most expensive first)
            high_end = self.get_queryset().order_by('-price')[:10]
            
            serializer = ProductListSerializer(high_end, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': high_end.count(),
                'message': 'High-end products retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error retrieving high-end products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve high-end products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_brand(self, request):
        """Get products by brand"""
        try:
            brand_name = request.query_params.get('brand', None)
            if not brand_name:
                return Response({
                    'success': False,
                    'message': 'Brand parameter is required',
                    'errors': {'brand': ['This field is required']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter products by brand name (case-insensitive)
            brand_products = self.get_queryset().filter(
                brand__name__icontains=brand_name
            ).order_by('-created_at')
            
            # Pagination
            page = self.paginate_queryset(brand_products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'products': serializer.data,
                    'brand': brand_name
                })
            
            serializer = ProductListSerializer(brand_products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': brand_products.count(),
                'brand': brand_name
            })
        except Exception as e:
            logger.error(f"Error retrieving products by brand: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve products by brand',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get products by category"""
        try:
            category_id = request.query_params.get('category_id', None)
            category_name = request.query_params.get('category_name', None)
            
            if not category_id and not category_name:
                return Response({
                    'success': False,
                    'message': 'Either category_id or category_name parameter is required',
                    'errors': {'category': ['category_id or category_name is required']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter products by category (including subcategories)
            if category_id:
                try:
                    from .models import Category
                    category = Category.objects.get(id=category_id)
                    category_ids = self.get_all_subcategories(category)
                    category_products = self.get_queryset().filter(category_id__in=category_ids)
                except Category.DoesNotExist:
                    category_products = self.get_queryset().none()
            else:
                try:
                    from .models import Category
                    # Find category by name and include its subcategories
                    category = Category.objects.filter(name__icontains=category_name).first()
                    if category:
                        category_ids = self.get_all_subcategories(category)
                        category_products = self.get_queryset().filter(category_id__in=category_ids)
                    else:
                        category_products = self.get_queryset().none()
                except Exception:
                    category_products = self.get_queryset().filter(
                        category__name__icontains=category_name
                    )
            
            category_products = category_products.order_by('-created_at')
            
            # Pagination
            page = self.paginate_queryset(category_products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'products': serializer.data,
                    'category_id': category_id,
                    'category_name': category_name
                })
            
            serializer = ProductListSerializer(category_products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': category_products.count(),
                'category_id': category_id,
                'category_name': category_name
            })
        except Exception as e:
            logger.error(f"Error retrieving products by category: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve products by category',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced product search"""
        try:
            query = request.query_params.get('q', '')
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            brand = request.query_params.get('brand')
            category = request.query_params.get('category')
            in_stock = request.query_params.get('in_stock', '').lower() == 'true'
            
            # Start with base queryset
            products = self.get_queryset()
            
            # Text search
            if query:
                products = products.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(brand__name__icontains=query) |
                    Q(category__name__icontains=query) |
                    Q(tags__name__icontains=query)
                ).distinct()
            
            # Price range filter
            if min_price:
                try:
                    products = products.filter(price__gte=float(min_price))
                except ValueError:
                    pass
            
            if max_price:
                try:
                    products = products.filter(price__lte=float(max_price))
                except ValueError:
                    pass
            
            # Brand filter
            if brand:
                products = products.filter(brand__name__icontains=brand)
            
            # Category filter
            if category:
                products = products.filter(category__name__icontains=category)
            
            # Stock filter
            if in_stock:
                products = products.filter(stock_quantity__gt=0)
            
            # Order by relevance (you can customize this logic)
            products = products.order_by('-created_at')
            
            # Pagination
            page = self.paginate_queryset(products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'products': serializer.data,
                    'search_params': {
                        'query': query,
                        'min_price': min_price,
                        'max_price': max_price,
                        'brand': brand,
                        'category': category,
                        'in_stock': in_stock
                    }
                })
            
            serializer = ProductListSerializer(products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': products.count(),
                'search_params': {
                    'query': query,
                    'min_price': min_price,
                    'max_price': max_price,
                    'brand': brand,
                    'category': category,
                    'in_stock': in_stock
                }
            })
        except Exception as e:
            logger.error(f"Error in product search: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to perform product search',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def price_range(self, request):
        """Get products within a specific price range"""
        try:
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            
            if not min_price and not max_price:
                return Response({
                    'success': False,
                    'message': 'At least one price parameter (min_price or max_price) is required',
                    'errors': {'price': ['min_price or max_price is required']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            products = self.get_queryset()
            
            # Apply price filters
            if min_price:
                try:
                    products = products.filter(price__gte=float(min_price))
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid min_price format',
                        'errors': {'min_price': ['Must be a valid number']}
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if max_price:
                try:
                    products = products.filter(price__lte=float(max_price))
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid max_price format',
                        'errors': {'max_price': ['Must be a valid number']}
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Order by price ascending
            products = products.order_by('price')
            
            # Pagination
            page = self.paginate_queryset(products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'products': serializer.data,
                    'price_range': {
                        'min_price': min_price,
                        'max_price': max_price
                    }
                })
            
            serializer = ProductListSerializer(products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': products.count(),
                'price_range': {
                    'min_price': min_price,
                    'max_price': max_price
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving products by price range: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve products by price range',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def product_collections(self, request):
        """Get all product collections and banners in a single response"""
        try:
            # Limit each collection to avoid large responses
            limit = int(request.query_params.get('limit', 10))
            
            # Get active banners
            banners = Banner.objects.filter(is_active=True).order_by('display_order', '-created_at')
            banners_serializer = BannerSerializer(banners, many=True)
            
            # Featured products (highest rated or most viewed)
            featured_products = self.get_queryset().filter(
                is_active=True
            ).order_by('-rating', '-product_views')[:limit]
            
            # Best sellers
            best_sellers = self.get_queryset().filter(
                quantity_sold__gt=0
            ).order_by('-quantity_sold')[:limit]
            
            # New arrivals
            new_arrivals = self.get_queryset().order_by('-created_at')[:limit]
            
            # Pocket friendly (cheapest products)
            pocket_friendly = self.get_queryset().order_by('price')[:limit]
            
            # High end (most expensive products)
            high_end = self.get_queryset().order_by('-price')[:limit]
            
            # New iPhones (Apple brand + iPhone category, sorted by latest)
            new_iphones = self.get_queryset().filter(
                brand__name__iexact='Apple',
                category__name__icontains='iPhone'
            ).order_by('-created_at')[:limit]
            
            # Apple Watches (Apple brand + Watch category, sorted by latest)
            apple_watches = self.get_queryset().filter(
                brand__name__iexact='Apple',
                category__name__icontains='Watch'
            ).order_by('-created_at')[:limit]
            
            # If no watches found by category, try product name
            if not apple_watches.exists():
                apple_watches = self.get_queryset().filter(
                    brand__name__iexact='Apple',
                    name__icontains='Watch'
                ).order_by('-created_at')[:limit]
            
            # Latest accessories (excluding Apple products)
            latest_accessories = self.get_queryset().filter(
                category__name__icontains='accessories'
            ).exclude(
                brand__name__iexact='Apple'
            ).order_by('-created_at')[:limit]
            
            # If no accessories found, try other accessory categories
            if not latest_accessories.exists():
                latest_accessories = self.get_queryset().filter(
                    category__name__iregex=r'(accessories|audio|storage|gaming|charger|powerbank)'
                ).exclude(
                    brand__name__iexact='Apple'
                ).order_by('-created_at')[:limit]
            
            # Gaming products (consoles, controllers, headsets, accessories)
            gaming_products = self.get_queryset().filter(
                category__name__iregex=r'(gaming|console|controller|headset)'
            ).order_by('-rating', '-created_at')[:limit]
            
            # If no gaming products found by category, try product names
            if not gaming_products.exists():
                gaming_products = self.get_queryset().filter(
                    name__iregex=r'(gaming|console|controller|headset|playstation|xbox|nintendo|razer|steelseries|corsair|hyperx)'
                ).order_by('-rating', '-created_at')[:limit]
            
            # Samsung products (Galaxy phones, tablets, watches, earbuds)
            samsung_products = self.get_queryset().filter(
                brand__name__iexact='Samsung'
            ).order_by('-created_at')[:limit]
            
            # If no Samsung products found by brand, try product names
            if not samsung_products.exists():
                samsung_products = self.get_queryset().filter(
                    name__iregex=r'(samsung|galaxy|note|tab|watch|buds)'
                ).order_by('-created_at')[:limit]
            
            # Infinix products (Infinix phones and accessories)
            infinix_products = self.get_queryset().filter(
                brand__name__iexact='Infinix'
            ).order_by('-created_at')[:limit]
            
            # If no Infinix products found by brand, try product names
            if not infinix_products.exists():
                infinix_products = self.get_queryset().filter(
                    name__iregex=r'(infinix|hot|note|zero|smart)'
                ).order_by('-created_at')[:limit]
            
            # Serialize all collections
            featured_serializer = ProductListSerializer(featured_products, many=True)
            best_sellers_serializer = ProductListSerializer(best_sellers, many=True)
            new_arrivals_serializer = ProductListSerializer(new_arrivals, many=True)
            pocket_friendly_serializer = ProductListSerializer(pocket_friendly, many=True)
            high_end_serializer = ProductListSerializer(high_end, many=True)
            new_iphones_serializer = ProductListSerializer(new_iphones, many=True)
            apple_watches_serializer = ProductListSerializer(apple_watches, many=True)
            latest_accessories_serializer = ProductListSerializer(latest_accessories, many=True)
            gaming_products_serializer = ProductListSerializer(gaming_products, many=True)
            samsung_products_serializer = ProductListSerializer(samsung_products, many=True)
            infinix_products_serializer = ProductListSerializer(infinix_products, many=True)
            
            return Response({
                'success': True,
                'banners': banners_serializer.data,
                'collections': {
                    'featured': {
                        'title': 'Featured Products',
                        'description': 'Highest rated and most viewed products',
                        'products': featured_serializer.data,
                        'count': featured_products.count()
                    },
                    'best_sellers': {
                        'title': 'Best Sellers',
                        'description': 'Our top selling products',
                        'products': best_sellers_serializer.data,
                        'count': best_sellers.count()
                    },
                    'new_arrivals': {
                        'title': 'New Arrivals',
                        'description': 'Latest products in our catalog',
                        'products': new_arrivals_serializer.data,
                        'count': new_arrivals.count()
                    },
                    'pocket_friendly': {
                        'title': 'Pocket Friendly',
                        'description': 'Affordable products for every budget',
                        'products': pocket_friendly_serializer.data,
                        'count': pocket_friendly.count()
                    },
                    'high_end': {
                        'title': 'High End',
                        'description': 'Premium products with top-tier features',
                        'products': high_end_serializer.data,
                        'count': high_end.count()
                    },
                    'new_iphones': {
                        'title': 'New iPhones',
                        'description': 'Latest iPhone models from Apple',
                        'products': new_iphones_serializer.data,
                        'count': new_iphones.count()
                    },
                    'apple_watches': {
                        'title': 'Apple Watches',
                        'description': 'Latest Apple Watch models',
                        'products': apple_watches_serializer.data,
                        'count': apple_watches.count()
                    },
                    'latest_accessories': {
                        'title': 'Latest Accessories',
                        'description': 'Newest accessories and add-ons',
                        'products': latest_accessories_serializer.data,
                        'count': latest_accessories.count()
                    },
                    'gaming_products': {
                        'title': 'Gaming Products',
                        'description': 'Gaming consoles, controllers, headsets and accessories',
                        'products': gaming_products_serializer.data,
                        'count': gaming_products.count()
                    },
                    'samsung_products': {
                        'title': 'Samsung Products',
                        'description': 'Latest Samsung Galaxy phones, tablets, watches and accessories',
                        'products': samsung_products_serializer.data,
                        'count': samsung_products.count()
                    },
                    'infinix_products': {
                        'title': 'Infinix Products',
                        'description': 'Latest Infinix smartphones and accessories',
                        'products': infinix_products_serializer.data,
                        'count': infinix_products.count()
                    }
                },
                'meta': {
                    'limit_per_collection': limit,
                    'total_collections': 11,
                    'total_banners': banners.count(),
                    'endpoints': {
                        'featured': '/api/products/featured/',
                        'best_sellers': '/api/products/best_sellers/',
                        'new_arrivals': '/api/products/new_arrivals/',
                        'pocket_friendly': '/api/products/pocket_friendly/',
                        'high_end': '/api/products/high_end/',
                        'new_iphones': '/api/products/new_iphones/',
                        'apple_watches': '/api/products/apple_watches/',
                        'latest_accessories': '/api/products/latest_accessories/',
                        'gaming_products': '/api/products/gaming_products/',
                        'samsung_products': '/api/products/samsung_products/',
                        'infinix_products': '/api/products/infinix_products/'
                    }
                },
                'message': 'Product collections and banners retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error retrieving product collections: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve product collections',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def samsung_products(self, request):
        """Get Samsung products (Galaxy phones, tablets, watches, earbuds)"""
        try:
            # Get limit from query params, default to 10
            limit = int(request.query_params.get('limit', 10))
            
            # First try to get Samsung products by brand
            samsung_products = self.get_queryset().filter(
                brand__name__iexact='Samsung'
            ).order_by('-created_at')[:limit]
            
            # If no Samsung brand found, try by product names
            if not samsung_products.exists():
                samsung_products = self.get_queryset().filter(
                    name__iregex=r'(samsung|galaxy|note|tab|watch|buds)'
                ).order_by('-created_at')[:limit]
            
            serializer = ProductListSerializer(samsung_products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': samsung_products.count(),
                'message': 'Samsung products retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error retrieving Samsung products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve Samsung products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def infinix_products(self, request):
        """Get Infinix products (Infinix smartphones and accessories)"""
        try:
            # Get limit from query params, default to 10
            limit = int(request.query_params.get('limit', 10))
            
            # First try to get Infinix products by brand
            infinix_products = self.get_queryset().filter(
                brand__name__iexact='Infinix'
            ).order_by('-created_at')[:limit]
            
            # If no Infinix brand found, try by product names
            if not infinix_products.exists():
                infinix_products = self.get_queryset().filter(
                    name__iregex=r'(infinix|hot|note|zero|smart)'
                ).order_by('-created_at')[:limit]
            
            serializer = ProductListSerializer(infinix_products, many=True)
            return Response({
                'success': True,
                'products': serializer.data,
                'count': infinix_products.count(),
                'message': 'Infinix products retrieved successfully'
            })
        except Exception as e:
            logger.error(f"Error retrieving Infinix products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve Infinix products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        """Override list method to add custom filtering including price range"""
        try:
            # Get query parameters
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            brand_ids = request.query_params.get('brand')
            category_ids = request.query_params.get('category')
            search_query = request.query_params.get('search')
            
            # Start with the base queryset
            queryset = self.filter_queryset(self.get_queryset())
            
            # Apply price filtering
            if min_price:
                try:
                    queryset = queryset.filter(price__gte=float(min_price))
                except ValueError:
                    pass
            
            if max_price:
                try:
                    queryset = queryset.filter(price__lte=float(max_price))
                except ValueError:
                    pass
            
            # Apply brand filtering (support multiple brands)
            if brand_ids:
                brand_id_list = [bid.strip() for bid in brand_ids.split(',') if bid.strip()]
                if brand_id_list:
                    try:
                        brand_id_list = [int(bid) for bid in brand_id_list]
                        queryset = queryset.filter(brand_id__in=brand_id_list)
                    except ValueError:
                        pass
            
            # Apply category filtering (support multiple categories)
            if category_ids:
                category_id_list = [cid.strip() for cid in category_ids.split(',') if cid.strip()]
                if category_id_list:
                    try:
                        category_id_list = [int(cid) for cid in category_id_list]
                        queryset = queryset.filter(category_id__in=category_id_list)
                    except ValueError:
                        pass
            
            # Apply search filtering
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(brand__name__icontains=search_query) |
                    Q(category__name__icontains=search_query)
                ).distinct()
            
            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in ProductViewSet list method: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve products',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """
        Override create method to add debug logging and handle image uploads
        """
        logger.debug(f"🔧 DEBUG: ProductViewSet.create() called")
        logger.debug(f"🔧 DEBUG: Request data: {request.data}")
        
        # Extract image files from request
        image_files = []
        for key, value in request.FILES.items():
            if key.startswith('image_'):
                image_files.append(value)
                logger.debug(f"🔧 DEBUG: Found image file: {key} -> {value.name}")
        
        serializer = self.get_serializer(data=request.data)
        logger.debug(f"🔧 DEBUG: Serializer created, checking validity")
        
        try:
            if serializer.is_valid():
                logger.debug(f"🔧 DEBUG: Serializer is valid, saving...")
                logger.debug(f"🔧 DEBUG: Validated data: {serializer.validated_data}")
                
                # Save the product first
                product = serializer.save()
                logger.debug(f"🔧 DEBUG: Product saved with ID: {product.id}")
                
                # Handle image uploads
                if image_files:
                    logger.debug(f"🔧 DEBUG: Processing {len(image_files)} image files")
                    self._handle_image_uploads(product, image_files)
                    
                    # Refresh the product instance to get updated images
                    product.refresh_from_db()
                
                headers = self.get_success_headers(serializer.data)
                # Return updated serializer data with images
                fresh_serializer = self.get_serializer(product)
                return Response(fresh_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                logger.debug(f"🔧 DEBUG: Serializer validation failed")
                logger.debug(f"🔧 DEBUG: Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"🔧 DEBUG: Exception in create: {e}")
            raise

    def update(self, request, *args, **kwargs):
        """
        Override update method to add debug logging and handle image uploads
        """
        logger.debug(f"🔧 DEBUG: ProductViewSet.update() called")
        logger.debug(f"🔧 DEBUG: Request data: {request.data}")
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        logger.debug(f"🔧 DEBUG: Updating product: {instance.name} (ID: {instance.id})")
        logger.debug(f"🔧 DEBUG: Current product type: {instance.product_type}")
        logger.debug(f"🔧 DEBUG: Current price: {instance.price}")
        
        # Extract image files from request
        image_files = []
        for key, value in request.FILES.items():
            if key.startswith('image_'):
                image_files.append(value)
                logger.debug(f"🔧 DEBUG: Found image file: {key} -> {value.name}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        logger.debug(f"🔧 DEBUG: Serializer created, checking validity")
        
        try:
            if serializer.is_valid():
                logger.debug(f"🔧 DEBUG: Serializer is valid, saving...")
                logger.debug(f"🔧 DEBUG: Validated data: {serializer.validated_data}")
                
                # Save the product
                product = serializer.save()
                logger.debug(f"🔧 DEBUG: Product updated")
                
                # Check if we should clear all existing images
                clear_existing = request.data.get('clear_existing_images')
                if clear_existing and clear_existing.lower() == 'true':
                    logger.debug(f"🔧 DEBUG: Clearing all existing images for product {product.id}")
                    from .models import ProductImage
                    deleted_count = ProductImage.objects.filter(product=product).count()
                    ProductImage.objects.filter(product=product).delete()
                    logger.debug(f"🔧 DEBUG: Cleared {deleted_count} existing images")
                
                # Handle removed images (for individual removals)
                removed_image_ids = request.data.get('removed_image_ids')
                if removed_image_ids:
                    try:
                        import json
                        removed_ids = json.loads(removed_image_ids) if isinstance(removed_image_ids, str) else removed_image_ids
                        logger.debug(f"🔧 DEBUG: Removing images with IDs: {removed_ids}")
                        
                        from .models import ProductImage
                        ProductImage.objects.filter(id__in=removed_ids, product=product).delete()
                        logger.debug(f"🔧 DEBUG: Removed {len(removed_ids)} images")
                    except Exception as e:
                        logger.error(f"🔧 DEBUG: Error removing images: {e}")
                
                # Handle image uploads (add new images, don't remove existing ones)
                if image_files:
                    logger.debug(f"🔧 DEBUG: Processing {len(image_files)} new image files")
                    self._handle_image_uploads(product, image_files)
                    
                    # Refresh the product instance to get updated images
                    product.refresh_from_db()
                
                if getattr(instance, '_prefetched_objects_cache', None):
                    instance._prefetched_objects_cache = {}
                
                # Return updated serializer data with fresh images
                fresh_serializer = self.get_serializer(product)
                return Response(fresh_serializer.data)
            else:
                logger.debug(f"🔧 DEBUG: Serializer validation failed")
                logger.debug(f"🔧 DEBUG: Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"🔧 DEBUG: Exception in update: {e}")
            raise

    def _handle_image_uploads(self, product, image_files):
        """
        Handle uploading multiple images for a product
        """
        from .models import ProductImage
        
        logger.debug(f"🔧 DEBUG: Creating ProductImage objects for product {product.id}")
        
        for i, image_file in enumerate(image_files):
            try:
                # Determine image type (first image is main, rest are gallery)
                image_type = 'main' if i == 0 and not product.product_images.filter(image_type='main').exists() else 'gallery'
                
                product_image = ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    image_type=image_type,
                    display_order=i,
                    alt_text=f"{product.name} - Image {i + 1}"
                )
                
                logger.debug(f"🔧 DEBUG: Created ProductImage {product_image.id} for {image_file.name}")
                
            except Exception as e:
                logger.error(f"🔧 DEBUG: Failed to create ProductImage for {image_file.name}: {e}")
                # Continue with other images even if one fails
                continue

    @action(detail=True, methods=['post'])
    def clear_images(self, request, pk=None):
        """
        Clear all images for a product
        """
        try:
            product = self.get_object()
            
            # Delete all ProductImage objects for this product
            deleted_count = ProductImage.objects.filter(product=product).count()
            ProductImage.objects.filter(product=product).delete()
            
            logger.debug(f"🔧 DEBUG: Cleared {deleted_count} images for product {product.id}")
            
            return Response({
                'success': True,
                'message': f'Cleared {deleted_count} images',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            logger.error(f"Error clearing images for product {pk}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to clear images',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductVariationViewSet(viewsets.ModelViewSet):
    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product']
    search_fields = ['sku', 'product__name']
    ordering_fields = ['product__name', 'sku', 'price', 'stock_quantity', 'created_at']
    ordering = ['product', 'sku']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'rating', 'is_approved']
    search_fields = ['review_text', 'product__name', 'user__email']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Users can only see approved reviews, staff can see all
        """
        if self.request.user.is_staff:
            return Review.objects.all()
        else:
            return Review.objects.filter(is_approved=True)

    def get_permissions(self):
        """
        Anyone can read reviews, authenticated users can create, 
        users can only update their own reviews, staff can do everything
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Set the user to the current user when creating a review
        """
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Only allow users to update their own reviews
        """
        instance = self.get_object()
        if not request.user.is_staff and instance.user != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied',
                'errors': {'detail': ['You can only update your own reviews']}
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Only allow users to delete their own reviews or staff
        """
        instance = self.get_object()
        if not request.user.is_staff and instance.user != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied',
                'errors': {'detail': ['You can only delete your own reviews']}
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.filter(is_active=True)
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'product_variation', 'image_type']
    search_fields = ['product__name', 'product_variation__sku', 'alt_text']
    ordering_fields = ['product__name', 'image_type', 'display_order', 'created_at']
    ordering = ['product', 'display_order', 'created_at']

    def get_permissions(self):
        """
        Read permissions for all, write permissions for staff only
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get images for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({
                'success': False,
                'message': 'Product ID is required',
                'errors': {'product_id': ['This parameter is required']}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            images = self.get_queryset().filter(
                product_id=product_id, 
                product_variation__isnull=True
            ).order_by('display_order', 'created_at')
            
            serializer = self.get_serializer(images, many=True)
            return Response({
                'success': True,
                'images': serializer.data,
                'count': images.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving product images: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve product images',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_variation(self, request):
        """Get images for a specific product variation"""
        variation_id = request.query_params.get('variation_id')
        if not variation_id:
            return Response({
                'success': False,
                'message': 'Variation ID is required',
                'errors': {'variation_id': ['This parameter is required']}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            images = self.get_queryset().filter(
                product_variation_id=variation_id
            ).order_by('display_order', 'created_at')
            
            serializer = self.get_serializer(images, many=True)
            return Response({
                'success': True,
                'images': serializer.data,
                'count': images.count()
            })
        except Exception as e:
            logger.error(f"Error retrieving variation images: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve variation images',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
