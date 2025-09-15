from .models import Lead, Offer, LeadScore
from .config import settings
import openai

# Configure OpenAI client
if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key":
    openai.api_key = settings.openai_api_key
else:
    # Handle the case where the API key is not set or is the default placeholder
    print("Warning: OpenAI API key is not configured. AI scoring will be disabled.")
    openai.api_key = None


def score_lead(lead: Lead, offer: Offer) -> LeadScore:
    """
    Scores a single lead based on rule-based logic and AI reasoning.
    """
    rule_score = 0
    
    # 1. Rule Layer
    # Role relevance
    role = lead.role.lower() if lead.role else ""
    if any(keyword in role for keyword in ['head', 'vp', 'director', 'manager', 'chief', 'founder', 'ceo', 'cto', 'cfo', 'coo']):
        rule_score += 20
    elif any(keyword in role for keyword in ['senior', 'lead', 'principal']):
        rule_score += 10

    # Industry match
    industry = lead.industry.lower() if lead.industry else ""
    if offer.ideal_use_cases and industry in [use_case.lower() for use_case in offer.ideal_use_cases]:
        rule_score += 20
    # A simple adjacent check
    elif offer.ideal_use_cases and any(keyword in industry for use_case in offer.ideal_use_cases for keyword in use_case.split()):
        rule_score += 10

    # Data completeness
    if all([lead.name, lead.role, lead.company, lead.industry, lead.location, lead.linkedin_bio]):
        rule_score += 10

    # 2. AI Layer
    ai_points = 0
    ai_reasoning = "AI scoring disabled or failed."
    intent = "Medium" # Default intent

    if openai.api_key:
        try:
            prompt = f"""
            Given the following product offer and prospect information, classify the prospect's buying intent as High, Medium, or Low. Also, provide a 1-2 sentence explanation for your classification.

            Product/Offer:
            - Name: {offer.name}
            - Value Propositions: {', '.join(offer.value_props)}
            - Ideal Use Cases: {', '.join(offer.ideal_use_cases)}

            Prospect:
            - Name: {lead.name}
            - Role: {lead.role}
            - Company: {lead.company}
            - Industry: {lead.industry}
            - Location: {lead.location}
            - LinkedIn Bio: {lead.linkedin_bio}

            Classification and Explanation:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in lead qualification."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5,
            )
            
            ai_response_text = response.choices[0].message['content'].strip()
            
            # Simple parsing of the response
            if "High" in ai_response_text:
                intent = "High"
                ai_points = 50
            elif "Medium" in ai_response_text:
                intent = "Medium"
                ai_points = 30
            elif "Low" in ai_response_text:
                intent = "Low"
                ai_points = 10
            
            # Extract reasoning
            # This is a simple way, could be improved with more robust parsing
            reasoning_parts = ai_response_text.split('\n')
            if len(reasoning_parts) > 1:
                ai_reasoning = ' '.join(reasoning_parts[1:])
            else:
                ai_reasoning = ai_response_text


        except Exception as e:
            print(f"Error during AI scoring: {e}")
            # Keep default values if AI scoring fails

    # 3. Final Score
    final_score = rule_score + ai_points

    # Determine final intent based on score if not set by AI
    if not openai.api_key:
        if final_score >= 70:
            intent = "High"
        elif final_score >= 40:
            intent = "Medium"
        else:
            intent = "Low"

    return LeadScore(
        **lead.dict(),
        intent=intent,
        score=final_score,
        reasoning=ai_reasoning if openai.api_key else "Rule-based score only."
    )
