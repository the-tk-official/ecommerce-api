import graphene

from product.schema import schema as product_schema
from user.schema import schema as user_schema


class Query(user_schema.Query, product_schema.Query, graphene.ObjectType):
    pass


class Mutation(user_schema.Mutation, product_schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
