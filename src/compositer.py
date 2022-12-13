from flask import Blueprint, Response, request, current_app
import json
import urllib 
import requests
import os
from CompositeResource import CompositeResource
import grequests

compositer = Blueprint('compositer', __name__)
SERVER_RECIPE = "localhost:5011"
SERVER_INGREDIENT = "localhost:5012"
if "api_endpoint_recipe" in os.environ:
   SERVER_RECIPE = os.environ["api_endpoint_recipe"]
if "api_endpoint_ingredient" in os.environ:
    SERVER_INGREDIENT = os.environ["api_endpoint_ingredient"]

def get_rsp_id(rsp, param_name, name, param_id):
    """get the id from rsp where dict[param_name] == name"""
    tmp = json.loads(rsp.response[0].decode())['Data']
    id = None
    if type(tmp) == list:
        for i in tmp:
            print(i[param_name])
            if i[param_name].lower() == name.lower(): 
                id = i[param_id]
            else: 
                print('No exact name')
    else:
        id = tmp[param_id]
    return id
        

@compositer.post("/compositer/<string:recipe_data>")
def add_recipes(recipe_data):
    """check wether the ingredients exist, add missing ingredients.
        return error if a recipe to be added already exists"""
    
    
    recipe_data = urllib.parse.parse_qs(urllib.parse.unquote(recipe_data))
    recipe_name = recipe_data['recipe_name'][0] if 'recipe_name' in recipe_data else None
    if recipe_name is None:
        return Response("INVALID CALL, MISSING RECIPE NAME", status=404, content_type="text/plain")
    data = request.get_json()
    print(data)
    ingredients = data["ingredients"]
    recipe_id = None
    ingredient_id = None

    # list get_urls to be called
    get_urls = [
        SERVER_RECIPE + f"/recipes?name/{recipe_name}"
    ]
    for ingredient in ingredients:
        get_urls.append(SERVER_INGREDIENT + f"/ingredient?name={ingredient}")

    # call all requests simultaneously
    reqs = (grequests.get(u) for u in get_urls)
    get_results = grequests.map(reqs)

    # return error if the recipe exists
    if (get_results[0].status_code == 200):
        return Response("RECIPE ALREADY EXISTS", status=404, content_type="text/plain")
    
    # api returns new recipe id
    recipe = requests.post(SERVER_RECIPE + f"/recipes/recipe_name={recipe_name}")
    ingredient_ids = list()
    # if recipe is successfully created proceed further
    if recipe.status_code == 200:
        # check missing ingredients and add to the ingredients database
        for i in range(len(ingredients)):
            if (get_results[i+1].status_code > 400):
                # ingredient name was not found, create a new ingredient
                new_ingredient = requests.post(SERVER_INGREDIENT + f"/ingredient/ingredient_name={ingredient}&description=None")
                print(new_ingredient.status_code,new_ingredient.json())
                if new_ingredient.status_code > 400:
                    return Response("ERROR ADDING INGREDIENTS", status=404, content_type="text/plain")
                ingredient_ids.append(new_ingredient.json()['Data'])
                #post_ingredients.append(SERVER + f"/ingredient/{ingredient}")
            else:
                ingredient_ids.append(get_results[i+1].json()['Data'][0]['ingredient_id'])
            

        # loop through ingredient ids and create ingredient_recipe map entry in the database
        post_map = list()
        for ingredient_id in ingredient_ids:
            post_map.append(SERVER_INGREDIENT + f"/ingredient/recipe_ingredient/recipe_id={recipe.json()['Data']}&ingredient_id={ingredient_id}")
        try:
            # create a map (recipe_id, ingredient_id)
            reqs = (grequests.post(u) for u in post_map)
            post_results = grequests.map(reqs)

            for result in post_results:
                if (result.status_code > 400):
                    return Response("ERROR MAPPING RECIPE TO INGREDIENTS", status=404, content_type="text/plain")
        except:
            return Response("ERROR MAPPING RECIPE TO INGREDIENTS", status=404, content_type="text/plain")

        rsp = Response(json.dumps({
            'Data': recipe.json()['Data'],
            'Links': [
                {
                    "href": f"/compositr/{recipe_name}",
                    "rel": "add new recipe",
                    "type": "POST"
                }
            ]
        }), status=200, content_type="text/plain")
    else:
        rsp = Response("ERROR ADDING RECIPE", status=404, content_type="text/plain")
    return rsp