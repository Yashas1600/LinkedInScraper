#!/usr/bin/env python3
"""
LinkedIn Profile Guessing Game

This program reads profile data from options.json and asks yes/no questions
to figure out which person you're thinking of from the scraped profiles.
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class ProfileGuesser:
    def __init__(self, profiles: List[Dict[str, Any]]):
        """Initialize the guesser with a list of profile data."""
        # Filter out profiles with errors
        self.profiles = [p for p in profiles if "error" not in p]
        self.remaining_profiles = self.profiles.copy()
        
        if not self.profiles:
            raise ValueError("No valid profiles found in data")
    
    def ask_question(self, question: str) -> bool:
        """Ask a yes/no question and return the answer."""
        while True:
            answer = input(f"{question} (yes/no): ").strip().lower()
            if answer in ['yes', 'y', 'true', '1']:
                return True
            elif answer in ['no', 'n', 'false', '0']:
                return False
            else:
                print("Please answer with 'yes' or 'no'")
    
    def filter_by_name(self, has_keyword: bool, keyword: str) -> None:
        """Filter profiles based on whether their name contains a keyword."""
        if has_keyword:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if keyword.lower() in p.get("full_name", "").lower()
            ]
        else:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if keyword.lower() not in p.get("full_name", "").lower()
            ]
    
    def filter_by_education(self, has_major: bool, major_keyword: str) -> None:
        """Filter profiles based on education major."""
        if has_major:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if any(
                    major_keyword.lower() in edu.get("major", "").lower()
                    for edu in p.get("education", [])
                )
            ]
        else:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if not any(
                    major_keyword.lower() in edu.get("major", "").lower()
                    for edu in p.get("education", [])
                )
            ]
    
    def filter_by_company(self, has_company: bool, company_keyword: str) -> None:
        """Filter profiles based on work experience at a company."""
        if has_company:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if any(
                    company_keyword.lower() in exp.get("company", "").lower()
                    for exp in p.get("experiences", [])
                )
            ]
        else:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if not any(
                    company_keyword.lower() in exp.get("company", "").lower()
                    for exp in p.get("experiences", [])
                )
            ]
    
    def filter_by_role(self, has_role: bool, role_keyword: str) -> None:
        """Filter profiles based on job role/title."""
        if has_role:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if any(
                    role_keyword.lower() in exp.get("role", "").lower()
                    for exp in p.get("experiences", [])
                )
            ]
        else:
            self.remaining_profiles = [
                p for p in self.remaining_profiles 
                if not any(
                    role_keyword.lower() in exp.get("role", "").lower()
                    for exp in p.get("experiences", [])
                )
            ]
    
    def get_unique_majors(self) -> List[str]:
        """Get list of unique majors from remaining profiles."""
        majors = set()
        for profile in self.remaining_profiles:
            for edu in profile.get("education", []):
                major = edu.get("major", "").strip()
                if major:
                    majors.add(major)
        return list(majors)
    
    def get_unique_companies(self) -> List[str]:
        """Get list of unique companies from remaining profiles."""
        companies = set()
        for profile in self.remaining_profiles:
            for exp in profile.get("experiences", []):
                company = exp.get("company", "").strip()
                if company:
                    companies.add(company)
        return list(companies)
    
    def get_unique_roles(self) -> List[str]:
        """Get list of unique roles from remaining profiles."""
        roles = set()
        for profile in self.remaining_profiles:
            for exp in profile.get("experiences", []):
                role = exp.get("role", "").strip()
                if role:
                    roles.add(role)
        return list(roles)
    
    def get_name_keywords(self) -> List[str]:
        """Get potential keywords from names."""
        keywords = set()
        for profile in self.remaining_profiles:
            name = profile.get("full_name", "")
            if name:
                # Split name into parts and add each part as a keyword
                parts = name.split()
                keywords.update(part for part in parts if len(part) > 2)
        return list(keywords)
    
    def choose_next_question(self) -> Optional[str]:
        """Choose the best question to ask next based on remaining profiles."""
        if len(self.remaining_profiles) <= 1:
            return None
        
        # Only ask about work experiences (companies and roles)
        companies = self.get_unique_companies()
        roles = self.get_unique_roles()
        
        # Randomly choose what type of question to ask
        question_types = []
        
        if companies:
            question_types.append(("company", random.choice(companies)))
        if roles:
            question_types.append(("role", random.choice(roles)))
        
        if not question_types:
            return None
        
        question_type, keyword = random.choice(question_types)
        
        if question_type == "company":
            return f"Has this person worked at {keyword}?"
        elif question_type == "role":
            return f"Has this person worked as a {keyword}?"
        
        return None
    
    def process_answer(self, question: str, answer: bool) -> None:
        """Process the answer to a question and filter profiles accordingly."""
        question_lower = question.lower()
        
        # Store the current number of remaining profiles before filtering
        before_count = len(self.remaining_profiles)
        
        if "worked at" in question_lower:
            # Company question
            keyword = question.split("worked at ")[-1].rstrip("?").strip()
            self.filter_by_company(answer, keyword)
        
        elif "worked as" in question_lower:
            # Role question
            keyword = question.split("worked as a ")[-1].rstrip("?").strip()
            self.filter_by_role(answer, keyword)
        
        # Check for contradictory answers (no profiles left)
        after_count = len(self.remaining_profiles)
        
        if after_count == 0 and before_count > 0:
            print("🤔 That answer doesn't make sense based on your previous answers!")
            print("Your answers seem to contradict each other.")
            print("Let me reset and we can start over, or you might have made a mistake.")
            
            # Reset to all profiles to continue the game
            self.remaining_profiles = self.profiles.copy()
            print("Starting fresh with all profiles...")
        
        elif after_count == before_count and before_count > 1:
            print("🤷 That question didn't help narrow things down - all remaining people match that answer.")
    
    def play_game(self) -> None:
        """Play the guessing game."""
        print(f"\n🎯 LinkedIn Profile Guessing Game!")
        print(f"Think of one person from the {len(self.profiles)} profiles I have.")
        print("I'll ask 5 yes/no questions about work experience to figure out who you're thinking of.\n")
        
        question_count = 0
        max_questions = 5
        
        while question_count < max_questions:
            question = self.choose_next_question()
            if not question:
                print("I'm out of good questions to ask!")
                break
            
            question_count += 1
            print(f"\nQuestion {question_count}/{max_questions}:")
            answer = self.ask_question(question)
            
            self.process_answer(question, answer)
            
            print(f"Remaining possibilities: {len(self.remaining_profiles)}")
            
            # Show remaining names if only a few left
            if len(self.remaining_profiles) <= 3:
                names = [p.get("full_name", "Unknown") for p in self.remaining_profiles]
                print(f"Could be: {', '.join(names)}")
            
            # Continue asking questions even if narrowed to 1 person
            if len(self.remaining_profiles) == 1:
                print("I have a strong guess, but let me ask a few more questions to be sure...")
        
        # Make final guess ONLY after all 5 questions are asked
        print(f"\n--- Finished asking {question_count} questions ---")
        
        if len(self.remaining_profiles) == 1:
            person = self.remaining_profiles[0]
            name = person.get("full_name", "Unknown Person")
            print(f"\n🎉 I think you're thinking of: {name}")
            
            # Show some details about the person
            print(f"\nHere's what I know about {name}:")
            print(f"LinkedIn: {person.get('linkedin_url', 'Unknown')}")
            
            # Fixed education handling
            if person.get("education"):
                print("Education:")
                education = person["education"]
                if isinstance(education, list):
                    for edu in education:
                        if isinstance(edu, dict):
                            major = edu.get("major", "Unknown major")
                            minor = edu.get("minor", "")
                            if minor:
                                print(f"  - {major} (Minor: {minor})")
                            else:
                                print(f"  - {major}")
                        else:
                            print(f"  - {edu}")
                else:
                    print(f"  - {education}")
            
            if person.get("experiences"):
                print("Experience:")
                for exp in person["experiences"][:3]:  # Show first 3 experiences
                    role = exp.get("role", "Unknown role")
                    company = exp.get("company", "Unknown company")
                    print(f"  - {role} at {company}")
            
            correct = self.ask_question("\nDid I guess correctly?")
            if correct:
                print("🎉 Yay! I guessed right!")
            else:
                print("😅 Oops! I was wrong. Good game though!")
        
        elif len(self.remaining_profiles) == 0:
            print("\n🤔 Hmm, I couldn't find anyone matching your answers.")
            print("Maybe there's an error in my data or I asked the wrong questions.")
        
        else:
            print(f"\n🤷 After {question_count} questions, I couldn't narrow it down to one person.")
            print(f"Could be any of these {len(self.remaining_profiles)} people:")
            for profile in self.remaining_profiles:
                print(f"  - {profile.get('full_name', 'Unknown')}")
            
            if len(self.remaining_profiles) <= 3:
                # Make a random guess from remaining options
                person = random.choice(self.remaining_profiles)
                name = person.get("full_name", "Unknown Person")
                print(f"\n🎲 I'll guess: {name}")
                
                correct = self.ask_question("Did I guess correctly?")
                if correct:
                    print("🎉 Lucky guess! I got it right!")
                else:
                    print("😅 Oops! Better luck next time!")


def load_profiles() -> List[Dict[str, Any]]:
    """Load profiles from options.json file."""
    options_file = Path(__file__).resolve().parent / "options.json"
    
    if not options_file.exists():
        print(f"Error: {options_file} not found!")
        print("Please run the scraper first with: python main.py")
        print("Choose 'names' and enter the names you want to scrape.")
        sys.exit(1)
    
    try:
        with open(options_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: options.json should contain a list of profiles")
            sys.exit(1)
        
        return data
    
    except json.JSONDecodeError as e:
        print(f"Error reading options.json: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading profiles: {e}")
        sys.exit(1)


def main():
    """Main function to run the guessing game."""
    try:
        profiles = load_profiles()
        
        if not profiles:
            print("No profiles found in options.json")
            sys.exit(1)
        
        # Filter out error profiles and show available profiles
        valid_profiles = [p for p in profiles if "error" not in p]
        
        if not valid_profiles:
            print("No valid profiles found (all had errors)")
            sys.exit(1)
        
        print(f"Loaded {len(valid_profiles)} profiles:")
        for i, profile in enumerate(valid_profiles, 1):
            name = profile.get("full_name", "Unknown")
            search_name = profile.get("search_name", "")
            if search_name and search_name != name:
                print(f"  {i}. {name} (searched as: {search_name})")
            else:
                print(f"  {i}. {name}")
        
        guesser = ProfileGuesser(profiles)
        guesser.play_game()
    
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
