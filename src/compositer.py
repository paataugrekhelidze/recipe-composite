from flask import Blueprint, Response, request, current_app
import json
import urllib 
import requests
import os

recipes = Blueprint('compositer', __name__)


@compositer.post("/compositer/<string:recipe_data>")
def add_recipes(recipe_data):
    """check wether the ingredients exist, add missing ingredients.
        return error if a recipe to be added already exists"""

    recipe_data = json.loads(urllib.parse.unquote(recipe_data))
    data = request.get_json()
    ingredients = data["ingredients"]

    # return error if the recipe exists
    if (requests.get(os.environ["api_endpoint"] + f"/recipes/name/{recipe_data}").status_code == 200):
        return Response("RECIPE ALREADY EXISTS", status=404, content_type="text/plain")

    # check missing ingredients and add to the ingredients database
    for ingredient in ingredients:
        if (requests.get(os.environ["api_endpoint"] + f"/ingredient/name/{ingredient}").status_code > 400):
            # ingredient name was not found, create a new ingredient
            requests.post(os.environ["api_endpoint"] + f"/ingredient/{ingredient}")

    # How to associate a list of ingredients?!
    add_recipe = requests.post(os.environ["api_endpoint"] + f"/recipes/{recipe_data}")

    # if recipe is successfully created return the success response
    if add_recipe.status_code == 200:
        rsp = Response(json.dumps({
            'Data': 'RECIPE ADDED',
            'Links': [
                {
                    "href": f"/compositr/{recipe_data}",
                    "rel": "add new recipe",
                    "type": "POST"
                }
            ]
        }), status=200, content_type="text/plain")
    else:
        rsp = Response("ERROR ADDING RECIPE", status=404, content_type="text/plain")

    return rsp
