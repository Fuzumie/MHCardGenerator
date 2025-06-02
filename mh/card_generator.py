import os
import json
import time
from selenium import webdriver
# Import Firefox-specific service and options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

def setup_driver():
    """Set up and return a Firefox webdriver with appropriate options."""
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")  # Run in headless mode (no UI)
    firefox_options.add_argument("--window-size=2000,1500")  # Larger window size to capture full cards
    # Firefox options might differ, disable-gpu and no-sandbox are typically Chrome-specific
    # firefox_options.add_argument("--disable-gpu")
    # firefox_options.add_argument("--no-sandbox")
    
    # You might need to specify the path to geckodriver if it's not in your PATH
    # service = FirefoxService(executable_path='/path/to/geckodriver')
    
    driver = webdriver.Firefox(options=firefox_options)
    print("Firefox driver initialized.")
    return driver

def load_monster_data():
    """Load monster data from all JSON files in the monsters directory."""
    print("Loading monster data...")
    monster_data = {}
    monsters_dir = os.path.join("src", "monsters")

    if not os.path.exists(monsters_dir):
        print(f"Error: Monsters directory not found at {monsters_dir}")
        return monster_data # Return empty if directory doesn't exist

    for filename in os.listdir(monsters_dir):
        if filename.endswith('.json'):
            monster_id = os.path.splitext(filename)[0]
            file_path = os.path.join(monsters_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                print(f"Loaded data for {monster_id}: {loaded_data.get(monster_id, {}).get('behavior', 'Behavior key not found or is not a list')}") # Print behavior list or status
                monster_data[monster_id] = loaded_data.get(monster_id, {})
                print(f"Processed monster data: {monster_id}")
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")

    if not monster_data:
        print("Warning: No monster data files found in src/monsters directory.")

    print(f"Finished loading {len(monster_data)} monsters.")
    return monster_data

def load_localization_data():
    """Load localization data from the en.json file."""
    print("Loading localization data...")
    file_path = os.path.join("src", "en.json")
    if not os.path.exists(file_path):
        print(f"Error: Localization file not found at {file_path}")
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Localization data loaded.")
    return data

def generate_cards(output_folder="generated_cards", monster_id_to_generate=None):
    """Generate card images for the specified monster and save them to the specified folder."""
    print("--- Starting generate_cards function ---")
    print(f"Starting card generation for monster '{monster_id_to_generate}' to folder: {output_folder}")
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Load data (still needed for behavior names and structure)
    monster_data = load_monster_data()
    localization_data = load_localization_data()
    titles = localization_data.get("monster-stat", {})

    # Setup webdriver
    print("Setting up webdriver...")
    driver = setup_driver()
    print("Webdriver setup complete.")

    try:
        # Navigate to the local development server
        print("Navigating to web page...")
        driver.get("http://localhost:5173")  # Assuming default Vite dev server port
        print("Waiting for page to load...")

        # Wait for the app to load (increased timeout)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".App"))
        )
        print(".App element found. Page loaded.")
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")

        # Check if we're in front view (default)
        is_front = True

        # --- Selenium interaction to select the monster ---
        if monster_id_to_generate:
            print(f"Attempting to select monster: {monster_id_to_generate}")
            # Wait for the selector dot to be present and clickable
            print("Waiting for selector dot...")
            selector_dot = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".monster-selector"))
            )
            print("Selector dot found and clickable.")
            print("Clicking selector dot...")
            selector_dot.click() # Click the dot to expand
            print("Selector dot clicked.")

            # Wait for the select element to become visible and enabled
            print("Waiting for select element...")
            select_element = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".monster-selector select"))
            )
            print("Select element found and visible.")

            # Use Select class to choose the option by value
            print(f"Attempting to select option with value: {monster_id_to_generate}")
            select = Select(select_element)
            select.select_by_value(monster_id_to_generate)
            print(f"Selected monster: {monster_id_to_generate}")

            # Add a longer explicit sleep after selection
            time.sleep(5) # Increased sleep time significantly
            print("Waited after monster selection.")

        # Wait for the monster cards to be loaded (for the selected monster)
        # Wait for at least one card element to appear
        print("Waiting for at least one card to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        print("At least one card element found.")
        time.sleep(2) # Add a buffer to ensure all cards are rendered

        # Get the currently displayed monster's data based on the selected ID
        current_monster_id = monster_id_to_generate # Use the provided ID
        current_monster = monster_data.get(current_monster_id)

        if not current_monster:
             raise Exception(f"Monster data not found for ID: {monster_id_to_generate}")

        print(f"\nProcessing currently displayed monster: {current_monster_id}")

        # Get behavior names for this monster
        behavior_names = current_monster.get("behavior-names", [])

        # If behavior names aren't available in the monster data, try to get from localization
        if not behavior_names and current_monster_id in titles:
            behavior_names = list(titles[current_monster_id].get("behavior", {}).values())

        # Track card names to detect duplicates within this monster's behaviors
        card_names_tracker = {} # Use a local tracker for this run

        # Find all cards on the page after selection and waiting
        print("Attempting to find card elements...")
        cards = driver.find_elements(By.CSS_SELECTOR, ".card")
        print(f"Found {len(cards)} card elements on the page.")

        # If no cards are found, take a screenshot for debugging (this is a fallback now)
        if not cards:
            print("No cards found.") # Keep a print statement
            return # Exit the function if no cards are found

        # Process each behavior card of the current monster
        print(f"Processing {len(cards)} found cards...")
        
        # Add print statements to inspect monster data and behavior list
        print(f"Current monster data structure: {type(current_monster)}")
        if isinstance(current_monster, dict):
            print(f"Current monster keys: {list(current_monster.keys())}")
            behavior_list = current_monster.get("behavior", [])
            print(f"Behavior list type: {type(behavior_list)}")
            if isinstance(behavior_list, list):
                print(f"Behavior list length: {len(behavior_list)}")
            else:
                print("'behavior' key does not contain a list.")
        else:
            print("Current monster is not a dictionary.")

        for i, behavior in enumerate(current_monster.get("behavior", [])):
            print(f"  Processing behavior index {i}...")
            # Ensure the index is within the range of found cards
            if i < len(cards):
                # Get the card name
                card_name = ""
                if i < len(behavior_names):
                    card_name = behavior_names[i]
                else:
                    # Use comment or ID as fallback
                    card_name = behavior.get("_comment1", f"behavior_{behavior.get('id', i)}")

                # Clean the filename
                safe_name = "".join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in card_name)
                safe_name = safe_name.replace(' ', '_')

                # Create filename
                filename = safe_name

                # Check for duplicate names within this monster's behaviors
                if card_name in card_names_tracker:
                     # This is a duplicate name - add the target or index as suffix
                    suffix = behavior.get("target", behavior.get("id", i))
                    filename = f"{safe_name}_{suffix}"
                    print(f"  Warning: Duplicate card name '{card_name}' for monster '{current_monster_id}'. Using filename '{filename}'")
                card_names_tracker[card_name] = filename # Track the name and its assigned filename

                print(f"  Processing card: {card_name}")

                # Make sure we're in front view for consistency
                if not is_front:
                    driver.execute_script("document.querySelector('.App').click();")
                    time.sleep(0.5)  # Wait for animation
                    is_front = True

                # Get the card element using the index from the found cards
                # We need to re-find cards here as the DOM might have changed after flipping
                cards_current_view = driver.find_elements(By.CSS_SELECTOR, ".card")

                if i < len(cards_current_view):
                    card_element = cards_current_view[i]

                    # Scroll to the card to ensure it's visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", card_element)
                    time.sleep(0.5)  # Wait for scroll

                    print(f"    Attempting to capture screenshot for {filename}_front.png")
                    # Take a screenshot of the front side
                    screenshot = card_element.screenshot_as_png
                    img = Image.open(BytesIO(screenshot))

                    # Save front side
                    front_path = os.path.join(output_folder, f"{filename}_front.png")
                    img.save(front_path)
                    print(f"    Saved front card: {front_path}")

                    # Click to flip card
                    driver.execute_script("document.querySelector('.App').click();")
                    time.sleep(1)  # Wait for animation
                    is_front = False

                    # Find all cards again after flip
                    cards_after_flip = driver.find_elements(By.CSS_SELECTOR, ".card")

                    # Ensure the index is within range of cards after flip
                    if i < len(cards_after_flip):
                        card_element_after_flip = cards_after_flip[i]

                        # Scroll to the card to ensure it's visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", card_element_after_flip)
                        time.sleep(0.5)  # Wait for scroll

                        print(f"    Attempting to capture screenshot for {filename}_back.png")
                        # Take screenshot of back side
                        screenshot = card_element_after_flip.screenshot_as_png
                        img = Image.open(BytesIO(screenshot))

                        # Save back side
                        back_path = os.path.join(output_folder, f"{filename}_back.png")
                        img.save(back_path)
                        print(f"    Saved back card: {back_path}")
                    else:
                        print(f"    Error: Card index {i} out of range after flip (total cards: {len(cards_after_flip)})")
                else:
                    print(f"    Error: Card index {i} out of range (total cards: {len(cards_current_view)})")

    except Exception as e:
        print(f"Error during card generation: {str(e)}")

    finally:
        # Clean up
        driver.quit()
        print("\nCard generation complete!")

def main():
    """Main function to run the card generator."""
    print("Monster Hunter Card Generator")
    print("===========================")
    
    # Set output folder to 'generated_cards' by default
    output_folder = "generated_cards"
    print(f"Output folder set to: {output_folder}")
        
    # Get monster ID from user
    monster_id_to_generate = input("Enter the ID of the monster to generate cards for (e.g., 'ark'): ").strip()
    if not monster_id_to_generate:
        print("No monster ID entered. Exiting.")
        return
    
    print(f"\nStarting card generation for monster '{monster_id_to_generate}' to folder: {output_folder}")
    generate_cards(output_folder, monster_id_to_generate)

if __name__ == "__main__":
    main()
