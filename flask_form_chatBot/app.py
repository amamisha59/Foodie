from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)

class Recipe(db.Model):
    recipe_id = db.Column(db.Integer, primary_key=True)
    recipe_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)
    cook_time = db.Column(db.Integer, nullable=False)
    total_time = db.Column(db.Integer, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=True)

class Ingredient(db.Model):
    ingredient_id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False, unique=True)

class RecipeIngredient(db.Model):
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.recipe_id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.ingredient_id'), primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    return render_template('add_recipe.html')

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    recipe_name = request.form['recipe_name']
    description = request.form.get('description')
    instructions = request.form['instructions']
    prep_time = request.form['prep_time']
    cook_time = request.form['cook_time']
    total_time = request.form['total_time']
    servings = request.form['servings']
    category = request.form.get('category')

    recipe = Recipe(
        recipe_name=recipe_name,
        description=description,
        instructions=instructions,
        prep_time=prep_time,
        cook_time=cook_time,
        total_time=total_time,
        servings=servings,
        category=category
    )
    db.session.add(recipe)
    db.session.commit()

    ingredient_names = request.form.getlist('ingredient_name[]')
    quantities = request.form.getlist('quantity[]')
    units = request.form.getlist('unit[]')

    for ingredient_name, quantity, unit in zip(ingredient_names, quantities, units):
        ingredient = Ingredient.query.filter_by(ingredient_name=ingredient_name).first()
        if not ingredient:
            ingredient = Ingredient(ingredient_name=ingredient_name)
            db.session.add(ingredient)
            db.session.commit()

        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.recipe_id,
            ingredient_id=ingredient.ingredient_id,
            quantity=quantity,
            unit=unit
        )
        db.session.add(recipe_ingredient)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    ingredients = [ingredient.strip().lower() for ingredient in data['ingredients'].split(',')]
    
    recipes = Recipe.query.join(RecipeIngredient).join(Ingredient).filter(
        Ingredient.ingredient_name.in_(ingredients)
    ).all()

    recipe_details = []
    for recipe in recipes:
        ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.recipe_id).all()
        ingredient_details = [
            {
                'name': Ingredient.query.filter_by(ingredient_id=ing.ingredient_id).first().ingredient_name,
                'quantity': ing.quantity,
                'unit': ing.unit
            }
            for ing in ingredients
        ]
        recipe_details.append({
            'recipe_name': recipe.recipe_name,
            'description': recipe.description,
            'instructions': recipe.instructions,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'total_time': recipe.total_time,
            'servings': recipe.servings,
            'category': recipe.category,
            'ingredients': ingredient_details
        })

    return jsonify({'recipes': recipe_details})

@app.route('/chatbot')
def chatbot():
    return render_template('chat.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)