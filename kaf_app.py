# kaf_app.py

import streamlit as st
import pandas as pd
import json
import os
import uuid
import csv

# --- Path Configuration ---
BEANS_DATA_PATH = 'datasets/coffee_beans.json'
RECIPES_DATA_PATH = 'datasets/brew_recipes.json'
TROUBLESHOOTING_KB_PATH = 'datasets/troubleshooting_knowledge_base.json'
DOCTOR_TRAINING_DATA_PATH = 'datasets/doctor_problem_training_data.csv'

# --- Helper Functions ---

def load_data(file_path, is_json=True):
    """Loads data from a JSON or CSV file."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            if is_json:
                return json.load(f)
            else: # Handle CSV
                return list(csv.reader(f))
    return [] if is_json else [['text', 'problem']] # Return header for new CSV

def save_data(file_path, data, is_json=True):
    """Saves data to a JSON or CSV file."""
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        if is_json:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else: # Handle CSV
            writer = csv.writer(f)
            writer.writerows(data)

def generate_unique_id(prefix):
    """Generates a simple unique ID."""
    return f"{prefix}_{str(uuid.uuid4())[:8]}"

def find_bean_by_id(beans_data, bean_id):
    """Find a bean by its ID."""
    return next((bean for bean in beans_data if bean['id'] == bean_id), None)

def find_recipe_by_id(recipes_data, recipe_id):
    """Find a recipe by its ID."""
    return next((recipe for recipe in recipes_data if recipe['recipe_id'] == recipe_id), None)

# --- Streamlit Application Interface ---

st.set_page_config(page_title="BaristaBox KAF", page_icon="🔧", layout="wide")
st.title("🔧 BaristaBox - Knowledge Acquisition Facility")
st.caption("Use this page to add, update, and manage the AI's knowledge base.")

# Load all existing data
beans_data = load_data(BEANS_DATA_PATH)
recipes_data = load_data(RECIPES_DATA_PATH)
troubleshooting_kb = load_data(TROUBLESHOOTING_KB_PATH)
doctor_training_data = load_data(DOCTOR_TRAINING_DATA_PATH, is_json=False)

# Create tabs
tab1, tab2, tab3 = st.tabs(["☕ Coffee Beans (Sommelier)", "📜 Brew Recipes (Brewer)", "🩺 Troubleshooting (Doctor)"])

# --- TAB 1: Coffee Bean Management ---
with tab1:
    st.header("Manage the Coffee Bean Database")
    
    # Create sub-tabs for different operations
    bean_tab1, bean_tab2, bean_tab3 = st.tabs(["➕ Add Bean", "✏️ Update Bean", "🗑️ Delete Bean"])
    
    with bean_tab1:
        st.subheader("Add a New Coffee Bean")
        with st.form("new_bean_form", clear_on_submit=True):
            name = st.text_input("Coffee Bean Name")
            origin = st.text_input("Country of Origin")
            coffee_type = st.selectbox("Coffee Type", ["Arabica", "Robusta", "Arabica/Robusta Blend"])
            roast_level = st.slider("Roast Level (1=Light, 5=Dark)", 1, 5, 3)
            processing = st.selectbox("Processing Method", ["Washed", "Natural", "Honey", "Wet-Hulled"])
            tasting_notes = st.text_area("Tasting Notes Profile")
            expert_tags_options = ["Fruity", "Floral", "Chocolatey", "Nutty", "Spicy", "Earthy", "Bright", "Balanced", "Bold", "Complex", "Classic", "Comforting", "Adventurous", "Morning Coffee", "Dessert Coffee"]
            expert_tags = st.multiselect("Expert Tags (for the AI)", options=expert_tags_options)
            
            submitted_bean = st.form_submit_button("Save New Coffee Bean")
            if submitted_bean:
                if not all([name, origin, tasting_notes, expert_tags]):
                    st.error("Please fill out all required fields.")
                else:
                    new_bean = {
                        "id": generate_unique_id("cb"),
                        "name": name,
                        "origin": origin,
                        "type": coffee_type,
                        "roast_level": roast_level,
                        "processing": processing,
                        "tasting_notes": tasting_notes,
                        "expert_tags": expert_tags
                    }
                    beans_data.append(new_bean)
                    save_data(BEANS_DATA_PATH, beans_data)
                    st.success(f"Successfully saved: {name}!")
                    st.rerun()
    
    with bean_tab2:
        st.subheader("Update an Existing Coffee Bean")
        if not beans_data:
            st.info("No coffee beans available to update.")
        else:
            bean_names = [f"{bean['name']} (ID: {bean['id']})" for bean in beans_data]
            selected_bean_display = st.selectbox("Select Bean to Update", options=bean_names, key="update_bean_select")
            
            if selected_bean_display:
                # Extract the ID from the display string
                selected_bean_id = selected_bean_display.split("ID: ")[1].rstrip(")")
                selected_bean = find_bean_by_id(beans_data, selected_bean_id)
                
                if selected_bean:
                    with st.form("update_bean_form"):
                        st.info(f"Updating: {selected_bean['name']}")
                        name = st.text_input("Coffee Bean Name", value=selected_bean['name'])
                        origin = st.text_input("Country of Origin", value=selected_bean['origin'])
                        coffee_type = st.selectbox("Coffee Type", 
                                                 ["Arabica", "Robusta", "Arabica/Robusta Blend"],
                                                 index=["Arabica", "Robusta", "Arabica/Robusta Blend"].index(selected_bean['type']))
                        roast_level = st.slider("Roast Level (1=Light, 5=Dark)", 1, 5, selected_bean['roast_level'])
                        processing = st.selectbox("Processing Method", 
                                                ["Washed", "Natural", "Honey", "Wet-Hulled"],
                                                index=["Washed", "Natural", "Honey", "Wet-Hulled"].index(selected_bean['processing']))
                        tasting_notes = st.text_area("Tasting Notes Profile", value=selected_bean['tasting_notes'])
                        expert_tags_options = ["Fruity", "Floral", "Chocolatey", "Nutty", "Spicy", "Earthy", "Bright", "Balanced", "Bold", "Complex", "Classic", "Comforting", "Adventurous", "Morning Coffee", "Dessert Coffee"]
                        expert_tags = st.multiselect("Expert Tags (for the AI)", 
                                                   options=expert_tags_options, 
                                                   default=selected_bean['expert_tags'])
                        
                        update_bean = st.form_submit_button("Update Coffee Bean")
                        if update_bean:
                            if not all([name, origin, tasting_notes, expert_tags]):
                                st.error("Please fill out all required fields.")
                            else:
                                # Update the bean data
                                for i, bean in enumerate(beans_data):
                                    if bean['id'] == selected_bean_id:
                                        beans_data[i] = {
                                            "id": selected_bean_id,
                                            "name": name,
                                            "origin": origin,
                                            "type": coffee_type,
                                            "roast_level": roast_level,
                                            "processing": processing,
                                            "tasting_notes": tasting_notes,
                                            "expert_tags": expert_tags
                                        }
                                        break
                                save_data(BEANS_DATA_PATH, beans_data)
                                st.success(f"Successfully updated: {name}!")
                                st.rerun()
    
    with bean_tab3:
        st.subheader("Delete a Coffee Bean")
        if not beans_data:
            st.info("No coffee beans available to delete.")
        else:
            st.warning("⚠️ Deleting a bean will also delete all associated recipes!")
            bean_names = [f"{bean['name']} (ID: {bean['id']})" for bean in beans_data]
            selected_bean_display = st.selectbox("Select Bean to Delete", options=bean_names, key="delete_bean_select")
            
            if selected_bean_display:
                selected_bean_id = selected_bean_display.split("ID: ")[1].rstrip(")")
                selected_bean = find_bean_by_id(beans_data, selected_bean_id)
                
                if selected_bean:
                    # Check for associated recipes
                    associated_recipes = [r for r in recipes_data if r['bean_id'] == selected_bean_id]
                    
                    st.info(f"Selected bean: {selected_bean['name']}")
                    if associated_recipes:
                        st.warning(f"This will also delete {len(associated_recipes)} associated recipe(s).")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Confirm Delete", type="secondary"):
                            # Remove the bean
                            beans_data[:] = [bean for bean in beans_data if bean['id'] != selected_bean_id]
                            # Remove associated recipes
                            recipes_data[:] = [recipe for recipe in recipes_data if recipe['bean_id'] != selected_bean_id]
                            
                            save_data(BEANS_DATA_PATH, beans_data)
                            save_data(RECIPES_DATA_PATH, recipes_data)
                            st.success(f"Successfully deleted: {selected_bean['name']} and {len(associated_recipes)} associated recipe(s)!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key="cancel_delete_bean"): # FIX: Added unique key
                            st.info("Delete operation cancelled.")

    st.subheader("Current Coffee Bean Database")
    if beans_data:
        df_display = pd.DataFrame(beans_data)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No coffee beans in the database.")

# --- TAB 2: Brew Recipe Management ---
with tab2:
    st.header("Manage Brew Recipes")
    
    # Create sub-tabs for different operations
    recipe_tab1, recipe_tab2, recipe_tab3 = st.tabs(["➕ Add Recipe", "✏️ Update Recipe", "🗑️ Delete Recipe"])
    
    with recipe_tab1:
        st.subheader("Add a New Brew Recipe")
        bean_name_to_id = {bean['name']: bean['id'] for bean in beans_data}
        if not bean_name_to_id:
            st.warning("Add a coffee bean in the 'Coffee Beans' tab before adding a recipe.")
        else:
            with st.form("new_recipe_form", clear_on_submit=True):
                selected_bean_name = st.selectbox("Select a Coffee Bean", options=bean_name_to_id.keys())
                brew_method = st.selectbox("Brew Method", ["V60", "AeroPress", "French Press", "Chemex", "Kalita Wave"])
                GRIND_SIZE_MAP = {
                    "Extra Coarse - Cold Brew": "Extra Coarse",
                    "Coarse - French Press": "Coarse",
                    "Medium-Coarse - Chemex": "Medium-Coarse",
                    "Medium - Drip Coffee": "Medium",
                    "Medium-Fine - V60": "Medium-Fine",
                    "Fine - Espresso": "Fine",
                    "Extra Fine - Turkish": "Extra Fine"
                }
                selected_grind_description = st.selectbox("Grind Size", options=list(GRIND_SIZE_MAP.keys()))
                coffee_grams = st.number_input("Coffee Weight (grams)", min_value=0.0, step=0.1, format="%.1f")
                water_grams = st.number_input("Water Weight (grams)", min_value=0, step=1)
                water_temp_c = st.number_input("Water Temperature (°C)", min_value=80, max_value=100, step=1)
                technique_notes = st.text_area("Expert Technique Notes")
                
                submitted_recipe = st.form_submit_button("Save New Recipe")
                if submitted_recipe:
                    if not all([selected_bean_name, brew_method, selected_grind_description, coffee_grams > 0, water_grams > 0]):
                        st.error("Please fill out all required fields.")
                    else:
                        bean_id = bean_name_to_id[selected_bean_name]
                        new_recipe = {
                            "recipe_id": generate_unique_id("br"),
                            "bean_id": bean_id,
                            "brew_method": brew_method,
                            "grind_size": GRIND_SIZE_MAP[selected_grind_description],
                            "coffee_grams": coffee_grams,
                            "water_grams": water_grams,
                            "water_temp_c": water_temp_c,
                            "technique_notes": technique_notes
                        }
                        recipes_data.append(new_recipe)
                        save_data(RECIPES_DATA_PATH, recipes_data)
                        st.success(f"Successfully saved recipe for {selected_bean_name}!")
                        st.rerun()
    
    with recipe_tab2:
        st.subheader("Update an Existing Recipe")
        if not recipes_data:
            st.info("No recipes available to update.")
        else:
            # Create display names for recipes
            id_to_bean_name = {bean['id']: bean['name'] for bean in beans_data}
            recipe_displays = []
            for recipe in recipes_data:
                bean_name = id_to_bean_name.get(recipe['bean_id'], 'Unknown Bean')
                recipe_displays.append(f"{bean_name} - {recipe['brew_method']} (ID: {recipe['recipe_id']})")
            
            selected_recipe_display = st.selectbox("Select Recipe to Update", options=recipe_displays, key="update_recipe_select")
            
            if selected_recipe_display:
                selected_recipe_id = selected_recipe_display.split("ID: ")[1].rstrip(")")
                selected_recipe = find_recipe_by_id(recipes_data, selected_recipe_id)
                
                if selected_recipe:
                    bean_name_to_id = {bean['name']: bean['id'] for bean in beans_data}
                    current_bean_name = id_to_bean_name.get(selected_recipe['bean_id'], 'Unknown Bean')
                    
                    with st.form("update_recipe_form"):
                        st.info(f"Updating recipe: {current_bean_name} - {selected_recipe['brew_method']}")
                        
                        selected_bean_name = st.selectbox("Select a Coffee Bean", 
                                                        options=list(bean_name_to_id.keys()),
                                                        index=list(bean_name_to_id.keys()).index(current_bean_name) if current_bean_name in bean_name_to_id else 0)
                        brew_method = st.selectbox("Brew Method", 
                                                 ["V60", "AeroPress", "French Press", "Chemex", "Kalita Wave"],
                                                 index=["V60", "AeroPress", "French Press", "Chemex", "Kalita Wave"].index(selected_recipe['brew_method']))
                        
                        GRIND_SIZE_MAP = {
                            "Extra Coarse - Cold Brew": "Extra Coarse",
                            "Coarse - French Press": "Coarse", 
                            "Medium-Coarse - Chemex": "Medium-Coarse",
                            "Medium - Drip Coffee": "Medium",
                            "Medium-Fine - V60": "Medium-Fine",
                            "Fine - Espresso": "Fine",
                            "Extra Fine - Turkish": "Extra Fine"
                        }
                        # Find current grind size key
                        current_grind_key = next((k for k, v in GRIND_SIZE_MAP.items() if v == selected_recipe['grind_size']), list(GRIND_SIZE_MAP.keys())[0])
                        selected_grind_description = st.selectbox("Grind Size", 
                                                                options=list(GRIND_SIZE_MAP.keys()),
                                                                index=list(GRIND_SIZE_MAP.keys()).index(current_grind_key))
                        
                        # FIX: Explicit type casting
                        coffee_grams = st.number_input("Coffee Weight (grams)", 
                                                     min_value=0.0, step=0.1, format="%.1f", 
                                                     value=float(selected_recipe['coffee_grams']))
                        water_grams = st.number_input("Water Weight (grams)", 
                                                    min_value=0, step=1, 
                                                    value=int(selected_recipe['water_grams']))
                        water_temp_c = st.number_input("Water Temperature (°C)", 
                                                     min_value=80, max_value=100, step=1, 
                                                     value=int(selected_recipe['water_temp_c']))
                        
                        technique_notes = st.text_area("Expert Technique Notes", value=selected_recipe['technique_notes'])
                        
                        update_recipe = st.form_submit_button("Update Recipe")
                        if update_recipe:
                            if not all([selected_bean_name, brew_method, selected_grind_description, coffee_grams > 0, water_grams > 0]):
                                st.error("Please fill out all required fields.")
                            else:
                                # Update the recipe data
                                for i, recipe in enumerate(recipes_data):
                                    if recipe['recipe_id'] == selected_recipe_id:
                                        recipes_data[i] = {
                                            "recipe_id": selected_recipe_id,
                                            "bean_id": bean_name_to_id[selected_bean_name],
                                            "brew_method": brew_method,
                                            "grind_size": GRIND_SIZE_MAP[selected_grind_description],
                                            "coffee_grams": coffee_grams,
                                            "water_grams": water_grams,
                                            "water_temp_c": water_temp_c,
                                            "technique_notes": technique_notes
                                        }
                                        break
                                save_data(RECIPES_DATA_PATH, recipes_data)
                                st.success(f"Successfully updated recipe for {selected_bean_name}!")
                                st.rerun()
    
    with recipe_tab3:
        st.subheader("Delete a Recipe")
        if not recipes_data:
            st.info("No recipes available to delete.")
        else:
            id_to_bean_name = {bean['id']: bean['name'] for bean in beans_data}
            recipe_displays = []
            for recipe in recipes_data:
                bean_name = id_to_bean_name.get(recipe['bean_id'], 'Unknown Bean')
                recipe_displays.append(f"{bean_name} - {recipe['brew_method']} (ID: {recipe['recipe_id']})")
            
            selected_recipe_display = st.selectbox("Select Recipe to Delete", options=recipe_displays, key="delete_recipe_select")
            
            if selected_recipe_display:
                selected_recipe_id = selected_recipe_display.split("ID: ")[1].rstrip(")")
                selected_recipe = find_recipe_by_id(recipes_data, selected_recipe_id)
                
                if selected_recipe:
                    bean_name = id_to_bean_name.get(selected_recipe['bean_id'], 'Unknown Bean')
                    st.info(f"Selected recipe: {bean_name} - {selected_recipe['brew_method']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Confirm Delete Recipe", type="secondary"):
                            recipes_data[:] = [recipe for recipe in recipes_data if recipe['recipe_id'] != selected_recipe_id]
                            save_data(RECIPES_DATA_PATH, recipes_data)
                            st.success(f"Successfully deleted recipe: {bean_name} - {selected_recipe['brew_method']}!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key="cancel_delete_recipe"): # FIX: Added unique key
                            st.info("Delete operation cancelled.")

    st.subheader("Current Brew Recipe Database")
    if recipes_data:
        df_recipes = pd.DataFrame(recipes_data)
        id_to_bean_name = {bean['id']: bean['name'] for bean in beans_data}
        df_recipes['bean_name'] = df_recipes['bean_id'].map(id_to_bean_name)
        display_df = df_recipes[['recipe_id', 'bean_name', 'brew_method', 'grind_size', 'coffee_grams', 'water_grams', 'water_temp_c', 'technique_notes']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("The brew recipe database is empty.")

# --- TAB 3: Troubleshooting Rule Management ---
with tab3:
    st.header("Manage Troubleshooting Rules (The Doctor's Brain)")
    
    # Create sub-tabs for different operations
    trouble_tab1, trouble_tab2, trouble_tab3, trouble_tab4 = st.tabs(["➕ Add Problem/Cause", "✏️ Update", "🗑️ Delete", "🧠 Training Data"])

    with trouble_tab1:
        st.subheader("Add New Problem or Cause")
        # --- FORM 1: Add a New Cause to a Problem ---
        with st.form("add_cause_form", clear_on_submit=True):
            st.subheader("Rule Details")
            
            # --- Select or Create a Problem Category ---
            existing_problems = list(troubleshooting_kb.keys())
            new_problem_option = "--- CREATE A NEW PROBLEM CATEGORY ---"
            problem_selection = st.selectbox(
                "Select a Problem to Add a Cause to", 
                options=existing_problems + [new_problem_option],
                key="cause_problem_select"
            )

            # --- Fields for a New Problem Category ---
            if problem_selection == new_problem_option:
                problem_key = st.text_input("New Problem Key (e.g., 'metallic', one word, lowercase)", key="new_problem_key")
                problem_description = st.text_area("Description of this new problem", key="new_problem_desc")
            else:
                problem_key = problem_selection

            st.markdown("---")
            # --- Fields for the New Cause ---
            cause_key = st.text_input("New Cause Key (e.g., 'grinder_dull', one word, lowercase)", key="new_cause_key")
            cause_question = st.text_area("Clarifying Question to Ask the User", key="new_cause_q")
            cause_solution = st.text_area("Actionable Solution to Provide", key="new_cause_s")
            
            submitted_cause = st.form_submit_button("Save New Cause")

            if submitted_cause:
                if not all([problem_key, cause_key, cause_question, cause_solution]):
                    st.error("Please fill out all fields to save a new cause.")
                else:
                    # Logic to Update Knowledge Base
                    if problem_key not in troubleshooting_kb:
                        if not problem_description:
                            st.error("A description is required when creating a new problem category.")
                        else:
                            troubleshooting_kb[problem_key] = {"description": problem_description, "causes": {}}
                    
                    troubleshooting_kb[problem_key]["causes"][cause_key] = {
                        "question": cause_question,
                        "solution": cause_solution
                    }
                    save_data(TROUBLESHOOTING_KB_PATH, troubleshooting_kb)
                    st.success(f"Successfully added new cause '{cause_key}' to '{problem_key}'!")
                    st.rerun()

    with trouble_tab2:
        st.subheader("Update Problems and Causes")
        
        if not troubleshooting_kb:
            st.info("No troubleshooting data available to update.")
        else:
            # Select problem to update
            update_problem = st.selectbox("Select Problem to Update", options=list(troubleshooting_kb.keys()), key="update_problem_select")
            
            if update_problem:
                update_type = st.radio("What do you want to update?", ["Problem Description", "Existing Cause"], key="update_type_radio")
                
                if update_type == "Problem Description":
                    with st.form("update_problem_desc_form"):
                        current_desc = troubleshooting_kb[update_problem].get("description", "")
                        new_description = st.text_area("Problem Description", value=current_desc)
                        
                        if st.form_submit_button("Update Problem Description"):
                            troubleshooting_kb[update_problem]["description"] = new_description
                            save_data(TROUBLESHOOTING_KB_PATH, troubleshooting_kb)
                            st.success(f"Updated description for '{update_problem}'!")
                            st.rerun()
                
                elif update_type == "Existing Cause":
                    causes = list(troubleshooting_kb[update_problem]["causes"].keys())
                    if not causes:
                        st.info("No causes available for this problem.")
                    else:
                        selected_cause = st.selectbox("Select Cause to Update", options=causes, key="update_cause_select")
                        
                        if selected_cause:
                            with st.form("update_cause_form"):
                                current_cause_data = troubleshooting_kb[update_problem]["causes"][selected_cause]
                                st.info(f"Updating cause: {selected_cause}")
                                
                                new_question = st.text_area("Clarifying Question", value=current_cause_data["question"])
                                new_solution = st.text_area("Solution", value=current_cause_data["solution"])
                                
                                if st.form_submit_button("Update Cause"):
                                    troubleshooting_kb[update_problem]["causes"][selected_cause] = {
                                        "question": new_question,
                                        "solution": new_solution
                                    }
                                    save_data(TROUBLESHOOTING_KB_PATH, troubleshooting_kb)
                                    st.success(f"Updated cause '{selected_cause}'!")
                                    st.rerun()

    with trouble_tab3:
        st.subheader("Delete Problems and Causes")
        
        if not troubleshooting_kb:
            st.info("No troubleshooting data available to delete.")
        else:
            delete_problem = st.selectbox("Select Problem", options=list(troubleshooting_kb.keys()), key="delete_problem_select")
            
            if delete_problem:
                delete_type = st.radio("What do you want to delete?", ["Entire Problem Category", "Specific Cause"], key="delete_type_radio")
                
                if delete_type == "Entire Problem Category":
                    st.warning(f"⚠️ This will delete the entire '{delete_problem}' problem category and all its causes!")
                    num_causes = len(troubleshooting_kb[delete_problem]["causes"])
                    st.info(f"This problem has {num_causes} cause(s).")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Confirm Delete Problem", type="secondary"):
                            # Also remove training data for this problem
                            doctor_training_data[:] = [row for row in doctor_training_data if row[0] == 'text' or (len(row) > 1 and row[1] != delete_problem)]
                            del troubleshooting_kb[delete_problem]
                            save_data(TROUBLESHOOTING_KB_PATH, troubleshooting_kb)
                            save_data(DOCTOR_TRAINING_DATA_PATH, doctor_training_data, is_json=False)
                            st.success(f"Deleted problem '{delete_problem}' and associated training data!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key="cancel_delete_problem"): # FIX: Added unique key
                            st.info("Delete operation cancelled.")
                
                elif delete_type == "Specific Cause":
                    causes = list(troubleshooting_kb[delete_problem]["causes"].keys())
                    if not causes:
                        st.info("No causes available for this problem.")
                    else:
                        delete_cause = st.selectbox("Select Cause to Delete", options=causes, key="delete_cause_select")
                        
                        if delete_cause:
                            st.info(f"Selected cause: {delete_cause}")
                            cause_data = troubleshooting_kb[delete_problem]["causes"][delete_cause]
                            st.text(f"Question: {cause_data['question']}")
                            st.text(f"Solution: {cause_data['solution']}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🗑️ Confirm Delete Cause", type="secondary"):
                                    del troubleshooting_kb[delete_problem]["causes"][delete_cause]
                                    save_data(TROUBLESHOOTING_KB_PATH, troubleshooting_kb)
                                    st.success(f"Deleted cause '{delete_cause}'!")
                                    st.rerun()
                            with col2:
                                if st.button("❌ Cancel", key="cancel_delete_cause"): # FIX: Added unique key
                                    st.info("Delete operation cancelled.")

    with trouble_tab4:
        st.subheader("Manage AI Training Data")
        
        # Add training examples
        with st.expander("🧠 Add Training Examples", expanded=True):
            with st.form("add_training_form", clear_on_submit=True):
                st.subheader("Improve the AI Classifier")

                # Select the problem you want to add examples for
                problem_to_train = st.selectbox(
                    "Select a Problem to Add Examples for",
                    options=list(troubleshooting_kb.keys()), # Can only add to existing problems
                    key="train_problem_select"
                )
                
                new_training_phrases = st.text_area(f"Add new example phrases for '{problem_to_train}', one per line.", key="new_phrases")

                submitted_phrases = st.form_submit_button("Save Training Phrases")

                if submitted_phrases:
                    if not new_training_phrases.strip():
                        st.error("Please enter at least one training phrase.")
                    else:
                        # Logic to Update Training Data
                        # Skip header row when checking existing data
                        existing_phrases = {tuple(row) for row in doctor_training_data[1:]}
                        phrases_added_count = 0
                        for phrase in new_training_phrases.strip().split('\n'):
                            if phrase.strip(): # Ensure not an empty line
                                new_row = (phrase.strip(), problem_to_train)
                                if new_row not in existing_phrases:
                                    doctor_training_data.append(list(new_row))
                                    phrases_added_count += 1
                        
                        if phrases_added_count > 0:
                            save_data(DOCTOR_TRAINING_DATA_PATH, doctor_training_data, is_json=False)
                            st.success(f"Successfully saved {phrases_added_count} new training phrase(s) for '{problem_to_train}'!")
                            st.rerun()
                        else:
                            st.warning("No new, unique phrases were added.")

        # Update/Delete training examples
        with st.expander("✏️ Manage Existing Training Data"):
            if len(doctor_training_data) <= 1:  # Only header or empty
                st.info("No training data available to manage.")
            else:
                training_rows = doctor_training_data[1:]  # Skip header
                df_training = pd.DataFrame(training_rows, columns=doctor_training_data[0])
                
                st.subheader("Current Training Data")
                st.dataframe(df_training, use_container_width=True)
                
                # Delete training examples
                st.subheader("Delete Training Examples")
                # Group training data by problem
                problems_with_counts = {}
                for row in training_rows:
                    if len(row) > 1:
                        problem = row[1]
                        if problem not in problems_with_counts:
                            problems_with_counts[problem] = []
                        problems_with_counts[problem].append(row[0])
                
                if problems_with_counts:
                    selected_problem_for_deletion = st.selectbox(
                        "Select Problem Category", 
                        options=list(problems_with_counts.keys()),
                        key="delete_training_problem_select"
                    )
                    
                    if selected_problem_for_deletion:
                        phrases_for_problem = problems_with_counts[selected_problem_for_deletion]
                        selected_phrases = st.multiselect(
                            f"Select phrases to delete from '{selected_problem_for_deletion}'",
                            options=phrases_for_problem,
                            key="delete_training_phrases_select"
                        )
                        
                        if selected_phrases:
                            if st.button("🗑️ Delete Selected Training Phrases", type="secondary"):
                                # Remove selected phrases
                                phrases_to_delete = set(selected_phrases)
                                new_training_data = [doctor_training_data[0]]  # Keep header
                                
                                for row in training_rows:
                                    if len(row) > 1 and not (row[1] == selected_problem_for_deletion and row[0] in phrases_to_delete):
                                        new_training_data.append(row)
                                
                                doctor_training_data.clear()
                                doctor_training_data.extend(new_training_data)
                                save_data(DOCTOR_TRAINING_DATA_PATH, doctor_training_data, is_json=False)
                                st.success(f"Deleted {len(selected_phrases)} training phrase(s)!")
                                st.rerun()

    # Display current knowledge base
    st.subheader("Current Troubleshooting Knowledge Base")
    if troubleshooting_kb:
        st.json(troubleshooting_kb, expanded=False)
    else:
        st.info("No troubleshooting data available.")

    st.markdown("---")
    st.subheader("Current AI Classifier Training Data Summary")
    
    if len(doctor_training_data) > 1:
        training_rows = doctor_training_data[1:]
        df_training = pd.DataFrame(training_rows, columns=doctor_training_data[0])
        
        # Show summary by problem
        if not df_training.empty and len(df_training.columns) > 1:
            problem_counts = df_training.iloc[:, 1].value_counts()
            st.write("Training examples per problem:")
            for problem, count in problem_counts.items():
                st.write(f"- {problem}: {count} examples")
            
            st.write(f"Total training examples: {len(training_rows)}")
        else:
            st.info("No valid training data structure found.")
    else:
        st.info("No training data has been added yet.")

# --- Footer Information ---
st.markdown("---")
st.markdown("### 📊 Knowledge Base Statistics")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Coffee Beans", len(beans_data))
with col2:
    st.metric("Brew Recipes", len(recipes_data))
with col3:
    st.metric("Problem Categories", len(troubleshooting_kb))
with col4:
    total_causes = sum(len(problem_data.get("causes", {})) for problem_data in troubleshooting_kb.values())
    st.metric("Total Causes", total_causes)

st.success("✅ Knowledge Acquisition Facility loaded successfully!")