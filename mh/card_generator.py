import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

def setup_driver():
    """Set up and return a Chrome webdriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--window-size=2000,1500")  # Larger window size to capture full cards
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def load_monster_data():
    """Load monster data from the monster.json file."""
    with open(os.path.join("src", "monster.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def load_localization_data():
    """Load localization data from the en.json file."""
    with open(os.path.join("src", "en.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def generate_cards(output_folder="generated_cards"):
    """Generate card images and save them to the specified folder."""
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    # Load data
    monster_data = load_monster_data()
    localization_data = load_localization_data()
    titles = localization_data.get("monster-stat", {})
    
    # Setup webdriver
    driver = setup_driver()
    
    try:
        # Navigate to the local development server
        driver.get("http://localhost:5173")  # Assuming default Vite dev server port
        print("Waiting for page to load...")
        
        # Wait for the app to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".App"))
        )
        
        # Add some CSS to ensure cards are properly sized and visible
        driver.execute_script("""
        var style = document.createElement('style');
        style.innerHTML = `
            .card { 
                transform: scale(1) !important; 
                margin: 20px !important; 
                display: block !important; 
            }
            .cards { 
                display: block !important; 
                width: auto !important; 
            }
            .App { 
                display: flex !important; 
                flex-direction: column !important; 
            }
        `;
        document.head.appendChild(style);
        """)  
        
        # Check if we're in front view (default)
        is_front = True
        
        # Process each monster
        for monster_id, monster_info in monster_data.items():
            print(f"\nProcessing monster: {monster_id}")
            
            # Get behavior names for this monster
            behavior_names = monster_info.get("behavior-names", [])
            
            # If behavior names aren't available in the monster data, try to get from localization
            if not behavior_names and monster_id in titles:
                behavior_names = list(titles[monster_id].get("behavior", {}).values())
            
            # Process each behavior card
            for i, behavior in enumerate(monster_info.get("behavior", [])):
                # Get the card name
                card_name = ""
                if i < len(behavior_names):
                    card_name = behavior_names[i]
                else:
                    # Use comment or ID as fallback
                    card_name = behavior.get("_comment1", f"behavior_{behavior.get('id', i)}")
                
                # Clean the filename - use only the attack move name
                safe_name = "".join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in card_name)
                safe_name = safe_name.replace(' ', '_')
                
                # Handle duplicate names by adding target or ID as suffix
                # Check if this is a duplicate name by looking at the behavior ID
                filename = safe_name
                
                # If it's one of the duplicate "Mending Lick" cards, add the target as suffix
                if card_name == "Mending Lick":
                    target = behavior.get("target", "")
                    if target:
                        filename = f"{safe_name}_{target}"
                
                print(f"  Processing card: {card_name}")
                
                # Make sure we're in front view for consistency
                if not is_front:
                    driver.execute_script("document.querySelector('.App').click();")
                    time.sleep(0.5)  # Wait for animation
                    is_front = True
                
                # Find all cards
                cards = driver.find_elements(By.CSS_SELECTOR, ".card")
                
                # Calculate the index of the current card (based on monster_id and behavior index)
                card_index = 0
                for m_id in monster_data:
                    if m_id == monster_id:
                        card_index += i
                        break
                    card_index += len(monster_data[m_id].get("behavior", []))
                
                # Ensure the index is within range
                if card_index < len(cards):
                    # Get the card element
                    card_element = cards[card_index]
                    
                    # Scroll to the card to ensure it's visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", card_element)
                    time.sleep(0.2)  # Wait for scroll
                    
                    # Take a screenshot of the front side
                    screenshot = card_element.screenshot_as_png
                    img = Image.open(BytesIO(screenshot))
                    
                    # Save front side
                    front_path = os.path.join(output_folder, f"{filename}_front.png")
                    img.save(front_path)
                    print(f"    Saved front card: {front_path}")
                    
                    # Click to flip card
                    driver.execute_script("document.querySelector('.App').click();")
                    time.sleep(0.5)  # Wait for animation
                    is_front = False
                    
                    # Get updated cards after flip
                    cards = driver.find_elements(By.CSS_SELECTOR, ".card")
                    
                    # Take screenshot of back side
                    if card_index < len(cards):
                        card_element = cards[card_index]
                        
                        # Scroll to the card to ensure it's visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", card_element)
                        time.sleep(0.2)  # Wait for scroll
                        
                        screenshot = card_element.screenshot_as_png
                        img = Image.open(BytesIO(screenshot))
                        
                        # Save back side
                        back_path = os.path.join(output_folder, f"{filename}_back.png")
                        img.save(back_path)
                        print(f"    Saved back card: {back_path}")
                else:
                    print(f"    Error: Card index {card_index} out of range (total cards: {len(cards)})")
    
    except Exception as e:
        print(f"Error during card generation: {str(e)}")
    
    finally:
        # Clean up
        driver.quit()
        print("\nCard generation complete!")

def main():
    """Main function to run the card generator."""
    print("Monster Hunter Card Generator")
    print("============================")
    
    # Check if development server is running
    output_folder = input("Enter output folder name (default: 'generated_cards'): ").strip()
    if not output_folder:
        output_folder = "generated_cards"
    
    print(f"\nStarting card generation to folder: {output_folder}")
    generate_cards(output_folder)

if __name__ == "__main__":
    main()
