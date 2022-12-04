from flask import Blueprint, Response, request, current_app
import json
import urllib 
import requests
import os

compositer = Blueprint('compositer', __name__)

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

    recipe_data = json.loads(urllib.parse.unquote(recipe_data))
    data = request.get_json()
    ingredients = data["ingredients"]
    recipe_id = None
    ingredient_id = None

    rsp = requests.get(os.environ["api_endpoint"] + f"/recipes/name/{recipe_data}")
    
    # return error if the recipe exists
    if (rsp.status_code == 200):
        return Response("RECIPE ALREADY EXISTS", status=404, content_type="text/plain")
    else:
        # get the recipe_id of recipe_data
        recipe_id = get_rsp_id(rsp, 'recipe_name', recipe_data, 'recipe_id')
    # check missing ingredients and add to the ingredients database
    for ingredient in ingredients:
        rsp1 = requests.get(os.environ["api_endpoint"] + f"/ingredient/name/{ingredient}")
        if (rsp1.status_code > 400):
            # ingredient name was not found, create a new ingredient
            ingredient_dict = {}
            ingredient_dict['ingredient_name'] = ingredient
            ingredient_dict['description'] = 'None'
            rsp2 = requests.post(os.environ["api_endpoint"] + f"/ingredient/{str(ingredient_dict)}")
            if (rsp2.status_code == 200):
                ingredient_id = get_rsp_id(rsp2, 'ingredient_name', ingredient, 'ingredient_id')
        else:
            if (rsp1.status_code == 200):
                ingredient_id = get_rsp_id(rsp1, 'ingredient_name', ingredient, 'ingredient_id')

    # How to associate a list of ingredients?!
    recipe_dict = {}
    recipe_dict['recipe_name'] = recipe_data
    recipe_dict['tags'] = 'None'
    recipe_dict['description'] = 'None'
    recipe_dict['picture'] = 'None'
    add_recipe = requests.post(os.environ["api_endpoint"] + f"/recipes/{str(recipe_dict)}")

    if recipe_id and ingredient_id:
        id_dict = {}
        id_dict['recipe_id'] = recipe_id
        id_dict['ingredient_id'] = ingredient_id
        add_recipe_ingredient = request.post(os.environ["api_endpoint"] + f"/recipe_ingredient/{str(id_dict)}")

    # if recipe is successfully created return the success response
    if add_recipe.status_code == 200 and add_recipe_ingredient.status_code == 200:
        rsp = Response(json.dumps({
            'Data': 'RECIPE ADDED',
            'Links': [
                {
                    "href": f"/compositer/{recipe_data}",
                    "rel": "add new recipe",
                    "type": "POST"
                }
            ]
        }), status=200, content_type="text/plain")
    else:
        rsp = Response("ERROR ADDING RECIPE", status=404, content_type="text/plain")

    return rsp
