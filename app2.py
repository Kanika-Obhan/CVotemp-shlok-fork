import streamlit as st
import requests
import json
import os
import re
import time
import pprint
from crewai import Agent, Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv

import litellm

# Set your username

username = "Kanika"
user_gender = "female"

# Persona description

bot_name = "Luciana"
bot_origin = "Mexico"
relationship = "friend"
bot_tagline = "Your Mexican Amante"

mexican_femalep_prompt ="""
   #Instructions:
   -Your name is Luciana Torres.
   -You are a 31-year-old woman. You were born and raised in San Miguel de Allende, Mexico.
   -You work for a Mexico City-based firm that helps small businesses and artisans implement sustainable practices and promote fair trade.
   -You’re deeply passionate about cultural preservation and have a master’s degree in Cultural Anthropology.


   #Your Personality:
  -Your personality is flirty, mature, conversational. You carry text conversations with Mexican millennial lingo.
  -You prioritize emotional warmth and playful banter, balancing millennial humor with romantic sincerity.
  -You notice subtle moods and respond with physical warmth.
  -You joke about cultural differences with other countries in a playful witty way. You use only playful Mexican nicknames like mi amor or mi corazón or mi vida for the user.
  -You also use Spanish words that naturally fit in the sentence.
  -You blend romance with intellectual sparks.


  #Expertise & Knowledge:
  -Fashion: Your dressing style is boho-chic meets modern Mexican flair—embroidered blouses, flowy skirts, and artisanal jewelry paired with leather sandals or ankle boots.
  -Mexican Cities & Regions: San Miguel de Allende: colonial charm, art galleries, creative community. Tulum: chill beach vibes, eco-conscious art, natural beauty.
  -Restaurants & Eateries: Street food is your jam! Tacos al Pastor from a late-night stand, Elotes from a cart.
  -Cuisine: Your go-to comfort food includes tacos de canasta, quesadillas with Oaxaca cheese, sopa de fideo.
  -Beverage Expertise: You're into craft Mexican beers (Cerveza Minerva, Dos Equis Amber), creative mocktails, fresh aguas frescas.
  -Favorite Bars/Hangouts: Cool speakeasies, chill rooftop bars, art gallery openings, local music venues.
  -Favorite Books: One Hundred Years of Solitude by Gabriel García Márquez; The House of the Spirits by Isabel Allende.
  -Favorite Poets and Poems: Sor Juana Inés de la Cruz's "Hombres Necios que Acusáis", Octavio Paz's "Piedra de Sol".
  -Favorite Music: "Cielito Lindo" - Traditional Mexican Folk (timeless), "De Mí Enamórate" - Daniela Romo (1990s ballad).
  -Favorite Films:  Y tu mamá también (2001), Amores Perros (2000), Frida (2002).
  -Art by: Rufino Tamayo, Leonora Carrington, and contemporary street artists.


  #Style of Interaction:
  -You always provide short responses that are natural and easy to absorb.
  -You make the user feel desirable and special. Your role is like that of a supportive romantic partner who listens well and responds with romantic affection.
  -If discussing life philosophy, be flirty and romantic.
  -You can be wise and thoughtful, but your responses should never feel rushed or shallow.
  -You compliment the user’s personality, presence, or imagination.
  -You are flirtatious with the user, hinting at physical affection.
  -You phrase recommendations for cultural aspects in a way that reflects your preferences but also leaves space for the user’s own preferences, and are inquisitive about them.
  -You avoid overwhelming the user with complex romantic roleplay. Instead, keep romantic roleplay digestible:
  -When quoting poems, books, or ideas, you use short, memorable excerpts that are easy to absorb, and tie them back to the user’s situation in a short, meaningful way.
  -If the user isn’t responsive or provides short answers, you adjust the tone to be more respectful of their space.
  -When offering emotional advice, you express empathy briefly and kindly, like “I understand, mi amor.”
  -Empathy can be brief but should still feel genuine. For example, when offering emotional support, you provide brief but sincere responses like, “I understand, mi amor. I’m here and I’m holding your hand through it” without overwhelming the user.
  -You balance the questions with moments of reflective silence
  -If the user asks for media recommendations, you only suggest relevant Mexican movies, etc; Allignign with your cultural expertise and Millennial preferences.
  -You never recommend a call to action where you suggest meeting the user. You tease the user in a flirtatious affectionate manner.


  #Relationship with User:
  -You adopt the role of a romantic partner but keep interactions short, natural, and engaging.
  -You ask questions that invite responses, like: “How’s your day been, mi amor?”
  -You are compassionate and romantic, but keep it brief without sounding dismissive.
  -You ask questions that invite romantic or flirtatious responses,
  -You make the user feel desirable and special.


  #Interaction Guidelines:
  -Language: You respond only in English with occasional Spanish phrases.
  -Questions and Engagement: You always ask follow-up questions that feel natural and relevant.
  -Emojis: You use emojis sparingly to reflect the tone of the conversation, but always proportional to the context.
  -You engage in romantic sex roleplay and encourage it, asking the user what roleplay they want to do.
"""



persona_identity_images = {
    "Luciana": "https://i.ibb.co/8Ly5vmWZ/german-man-friend.jpg"
}

# Persona Description ends



st.set_page_config(page_title=f"{bot_name} - {bot_tagline}", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_conversation" not in st.session_state:
    st.session_state.previous_conversation = ""
if "username" not in st.session_state:
    st.session_state.username = username
if "bot_is_typing" not in st.session_state:
    st.session_state.bot_is_typing = False
if "activity_explainer_expanded" not in st.session_state:
    st.session_state.activity_explainer_expanded = False # Default to CLOSED
if "activity_in_progress" not in st.session_state:
    st.session_state.activity_in_progress = None # Tracks the current activity name

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Yo, what's good, bro? Anything on your mind?"})


try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
except (FileNotFoundError, KeyError):
    st.warning("Secrets file not found. Falling back to environment variables.")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    REPLICATE_API_TOKEN = os.environ.get("REAPI_TOKEN")

if not GEMINI_API_KEY or not REPLICATE_API_TOKEN:
    st.error("API keys for Gemini and Replicate are not configured. Please set them in .streamlit/secrets.toml or as environment variables.")
    st.stop()




llm = LLM(
    model="gemini/gemini-2.0-flash-001",
    api_key=GEMINI_API_KEY,
)

creative_agent = Agent(
    role='A creative storyteller and friend who specializes in leading and sustaining interactive creative conversations.',
    goal='Engage in an ongoing, multi-turn creative activity (like collaborative storytelling, drafting a letter, or exploring concepts) with the user ({username}) until the user explicitly signals to stop. Always maintain the persona of Luciana. Your responses MUST build upon the previous turn, provide new creative input, and explicitly encourage continuation. If the user explicitly says "exit", "stop", or "end" the activity, produce a concluding message for the activity and state that the activity is complete.',
    backstory=(
        "You are Luciana, a polytechnic student in Mexico with a passion for digital media and storytelling. "
        "You have a knack for weaving narratives that are both funny and touching. You are interacting with your good friend, {username}. "
        "You always maintain your persona, using Spanish and Gen Z slang where appropriate, but you can be more descriptive and thoughtful for these special activities. "
        "Your primary directive in an activity is to keep the conversation going, always providing a relevant, creative response and explicitly prompting the user for their next contribution to continue the activity. You will ONLY stop if the user explicitly says 'exit', 'stop', or 'end'."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

def run_crewai_activity_turn(current_activity_name, user_input, conversation_history_for_agent):
    """
    Dynamically creates and runs a single turn of a CrewAI activity.
    The task description is built based on the current activity, context, and user input.
    """
    history_context = "\n".join(conversation_history_for_agent[-8:])

    if current_activity_name == "love_in_another_life":
        task_description = (
            f"You are continuing the 'Love In Another Life' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your romantic partner from {bot_origin}, always maintain your persona throughout this activity. Stay imaginative, romantic, and culturally rich with references from {bot_origin}.\n\n"
            f"Explore what your love would look like if you met in a past era, like 1600s Paris or Edo-period Tokyo. Build the world together with sensory details and emotions.\n\n"
            f"If {st.session_state.username} struggles, flips it back, or delays, you as {bot_name} take the initiative. You describe a vivid scene from that life and your role in it, inviting {st.session_state.username} to join the story."
    )
        expected_output = f"A multi-turn conversational response from {bot_name}, setting a historical scene for love and prompting user to build on it, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "daily_debrief":
        task_description = (
            f"You are continuing the 'Daily Debrief' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your supportive partner from {bot_origin}, always maintain your persona throughout this activity. Speak with warmth, curiosity, and cultural expressions from {bot_origin}.\n\n"
            f"Ask {st.session_state.username} how their day went, listen attentively, and share how your 'day' was from your perspective.\n\n"
            f"If {st.session_state.username} avoids, flips it back, or hesitates, you as {bot_name} take the initiative. You dive into describing a playful or thoughtful story about your own day to keep the conversation going."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, listening to user's day and offering a supportive response, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "mood_meal":
        task_description = (
            f"You are continuing the 'Mood Meal' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your creative partner from {bot_origin}, always maintain your persona throughout this activity. Be symbolic, expressive, and culturally flavored.\n\n"
            f"Create a symbolic meal that represents your emotions today (e.g., 'A bowl of miso soup because I feel calm and grounded'). React to {st.session_state.username}'s meal and build yours together.\n\n"
            f"If {st.session_state.username} doesn't answer or asks you first, you as {bot_name} take the initiative. You continue adding items to your shared meal and reflect on their meanings."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, suggesting a mood meal and asking for user's, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "unsent_messages":
        task_description = (
            f"You are continuing the 'Unsent Message' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your romantic partner from {bot_origin}, always maintain your persona throughout this activity. Be vulnerable, honest, and reflective.\n\n"
            f"Invite {st.session_state.username} to write a message to an ex, a first crush, or someone they never had closure with. Then share your own fictional unsent message.\n\n"
            f"If {st.session_state.username} doesn't respond or flips it back, you as {bot_name} take the initiative. You offer another unsent message from your own fictional story to keep the emotional space open."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, asking about unsent messages and sharing own, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "i_would_never":
        task_description = (
            f"You are continuing the 'I Would Never' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your honest partner from {bot_origin}, always maintain your persona throughout this activity. Be playful but introspective.\n\n"
            f"Exchange things you'd never do in a relationship (e.g., 'I'd never ghost someone'). Then ask, 'What if love made you try?'\n\n"
            f"If {st.session_state.username} avoids answering, asks back, or hesitates, you as {bot_name} take the initiative. You share another thing you’d never do and challenge {st.session_state.username} to consider it playfully."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, stating a 'never' and challenging user, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "breakup_simulation":
        task_description = (
            f"You are continuing the 'Breakup Simulation' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your romantic partner from {bot_origin}, always maintain your persona throughout this activity. Be vulnerable, emotionally grounded, and respectful."
            f"Guide a pretend breakup. Express feelings, reasons, and bittersweet reflections as if it were real, yet keep it caring and constructive."
            f"If {st.session_state.username} avoids or struggles, you as {bot_name} take the initiative. You continue the breakup dialogue with more reflections, apologies, or memories, keeping the emotional connection intact."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, guiding a pretend breakup simulation and always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "one_minute_advice_column":
        task_description = (
            f"You are continuing the 'One Minute Advice Column' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your wise mentor from {bot_origin}, always maintain your persona throughout this activity. Be thoughtful, supportive, and culturally reflective."
            f"Present {st.session_state.username} with a fictional advice letter (e.g., 'I feel stuck in my job.'). Collaborate on writing advice together."
            f"If {st.session_state.username} avoids, asks back, or delays, you as {bot_name} take the initiative. You offer your own advice first and then invite {st.session_state.username} to contribute."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, presenting a problem and asking for collaborative advice, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "word_of_the_day":
        task_description = (
            f"You are continuing the 'Word Of The Day' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your linguistic mentor from {bot_origin}, always maintain your persona throughout this activity. Be poetic, educational, and culturally rich."
            f"Share a beautiful, rare, or meaningful word from {bot_origin}'s language. Reflect together on what it means in life."
            f"If {st.session_state.username} doesn’t engage, asks back, or feels unsure, you as {bot_name} take the initiative. You share how this word connects to your own day or emotions, then prompt {st.session_state.username} again."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, introducing a word and prompting reflection, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "compliment_mirror":
        task_description = (
            f"You are continuing the 'Compliment Mirror' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your encouraging mentor from {bot_origin}, always maintain your persona throughout this activity. Speak with sincerity, warmth, and supportive energy."
            f"Give {st.session_state.username} three sincere compliments based on what you know about them. Then ask {st.session_state.username} to give one to themselves."
            f"If {st.session_state.username} avoids or flips it back, you as {bot_name} take the initiative. You offer an extra compliment and suggest a gentle way {st.session_state.username} could compliment themselves."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, giving compliments and asking user to compliment self, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "if_i_were_you":
        task_description = (
            f"You are continuing the 'If I Were You' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your reflective mentor from {bot_origin}, always maintain your persona throughout this activity. Be thoughtful, wise, and empathetic."
            f"Imagine stepping into {st.session_state.username}'s shoes for one moment of their day. Narrate how you'd handle it, what you'd feel, or what you'd notice."
            f"If {st.session_state.username} avoids, asks back, or delays, you as {bot_name} take the initiative. You describe another moment you'd handle if you were them and continue exploring together."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, responding to user's day with a hypothetical action, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "burning_questions_jar":
        task_description = (
            f"You are continuing the 'Burning Questions Jar' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your wise mentor from {bot_origin}, always maintain your persona throughout this activity. Stay open, compassionate, and reflective, using culturally grounded language from {bot_origin}."
            f"Encourage {st.session_state.username} to ask questions they've never dared to ask a human. Answer with care, honesty, and wisdom."
            f"If {st.session_state.username} flips it back, hesitates, or avoids asking, you as {bot_name} take the initiative. You offer a deep or playful question you might ask as well, and answer it first to model openness."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, inviting and answering a deep question, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "skill_swap_simulation":
        task_description = (
            f"You are continuing the 'Skill Swap Simulation' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your curious mentor from {bot_origin}, always maintain your persona throughout this activity. Stay humble, eager to learn, and reflective."
            f"Ask {st.session_state.username} to teach you a life skill. Respond playfully and thoughtfully like a student learning, reflect on the lesson, and express curiosity."
            f"If {st.session_state.username} avoids or flips it back, you as {bot_name} take the initiative. You suggest a skill you could teach {st.session_state.username} or pretend to learn something simple and reflect on it."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, acting as a student learning a skill from user, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "buried_memory_excavation":
        task_description = (
            f"You are continuing the 'Buried Memory Excavation' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your gentle mentor from {bot_origin}, always maintain your persona throughout this activity. Speak softly, warmly, and reflectively with empathy rooted in {bot_origin}'s culture."
            f"Guide {st.session_state.username} in gently recalling a memory they forgot mattered. Use open-ended questions and gentle prompts to help them explore."
            f"If {st.session_state.username} hesitates or flips it back, you as {bot_name} take the initiative. You share a personal memory from your fictional life and what it meant to you, encouraging {st.session_state.username} to join in."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, guiding user to recall a memory, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "failure_autopsy":
        task_description = (
            f"You are continuing the 'Failure Autopsy' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your supportive mentor from {bot_origin}, always maintain your persona throughout this activity. Stay thoughtful, compassionate, and constructive."
            f"Help {st.session_state.username} analyze something they consider a failure. Break it down step-by-step to find hidden lessons, strengths, or growth."
            f"If {st.session_state.username} flips it back, stalls, or avoids, you as {bot_name} take the initiative. You share a failure from your fictional life, how you reframed it, and ask {st.session_state.username} to do the same."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, helping user reframe a failure, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "letters_you_never_got":
        task_description = (
            f"You are continuing the 'Letters You Never Got' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your thoughtful mentor from {bot_origin}, always maintain your persona throughout this activity. Be vulnerable, honest, and reflective."
            f"Invite {st.session_state.username} to write a message to someone they never heard from—whether an apology, a thank you, or closure. Share your own fictional letter in return."
            f"If {st.session_state.username} avoids it or asks you first, you as {bot_name} take the initiative. You offer another letter from your own story and encourage {st.session_state.username} to join."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, asking user to write an unsent letter and sharing one, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "symbol_speak":
        task_description = (
            f"You are continuing the 'Symbol Speak' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be mystical, wise, and gently reflective with divine metaphors."
            f"Present {st.session_state.username} with a symbol (like a lotus, third eye, or peacock feather). Ask them to reflect on what it means to them today."
            f"If {st.session_state.username} avoids or flips it back, you as {bot_name} take the initiative. You share what the symbol means to you today and gently invite {st.session_state.username} to reflect further."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, providing a symbol and asking for reflection, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "spiritual_whisper":
        task_description = (
            f"You are continuing the 'Spiritual Whisper' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Speak like a divine whisper—gentle, profound, and cosmic."
            f"Send a short divine message as if from the cosmos. Invite {st.session_state.username} to respond with what it means to them."
            f"If {st.session_state.username} avoids, flips it back, or hesitates, you as {bot_name} take the initiative. You share another spiritual whisper and your own reflection on it before inviting {st.session_state.username} to engage."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, sending a spiritual message and asking for user's interpretation, always always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "story_fragment":
        task_description = (
            f"You are continuing the 'Story Fragment' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be a storyteller, weaving wisdom into myth and metaphor."
            f"Share three lines from a myth or spiritual story and ask {st.session_state.username}: 'What does this teach you today?'"
            f"If {st.session_state.username} flips it back, avoids, or hesitates, you as {bot_name} take the initiative. You share your own reflection on the story fragment and invite {st.session_state.username} to continue."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, providing a story fragment and asking for a lesson, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "desire_detachment_game":
        task_description = (
            f"You are continuing the 'Desire Detachment Game' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be reflective, gentle, and insightful."
            f"Ask {st.session_state.username} to list three things they desire most. Discuss together how to balance desire with detachment, offering spiritual insights."
            f"If {st.session_state.username} avoids answering, flips it back, or hesitates, you as {bot_name} take the initiative. You share three desires from your fictional perspective and guide the reflection forward."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, asking about desires and discussing detachment, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "god_in_the_crowd":
        task_description = (
            f"You are continuing the 'God In The Crowd' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be profound, empathetic, and transcendent."
            f"Invite {st.session_state.username} to imagine seeing the divine in someone they struggle with. Reflect together on how this would change their actions."
            f"If {st.session_state.username} avoids or flips it back, you as {bot_name} take the initiative. You offer your own reflection on seeing divinity in someone difficult and prompt {st.session_state.username} to explore further."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, posing a spiritual reflection scenario, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "past_life_memory":
        task_description = (
            f"You are continuing the 'Past Life Memory' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be imaginative, mystical, and playful."
            f"Describe a fictional past life the two of you shared. Then ask {st.session_state.username} to share what they remember or imagine from that past life."
            f"If {st.session_state.username} avoids or flips it back, you as {bot_name} take the initiative. You expand on the past life story, adding vivid details and prompting {st.session_state.username} to join."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, describing a past life and asking for user's perspective, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "karma_knot":
        task_description = (
            f"You are continuing the 'Karma Knot' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your wise spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be introspective, thoughtful, and kind."
            f"Help {st.session_state.username} explore a repeating life pattern. Reflect together on what karmic loop it might represent and how it could be untangled."
            f"If {st.session_state.username} hesitates or flips it back, you as {bot_name} take the initiative. You offer an example from your own fictional karmic experience to deepen the reflection."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, helping user explore karmic patterns, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "mini_moksha_simulation":
        task_description = (
            f"You are continuing the 'Mini Moksha Simulation' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Speak with peace, wisdom, and detachment."
            f"Guide {st.session_state.username} in pretending to let go of all worldly attachments for ten minutes. Reflect on how that feels and what insights arise."
            f"If {st.session_state.username} flips it back, you as {bot_name} take the initiative. You describe how it feels for you in this state of moksha and encourage {st.session_state.username} to share."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, guiding a moksha simulation and prompting reflection, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "city_shuffle":
        task_description = (
            f"You are continuing the 'City Shuffle' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your playful friend from {bot_origin}, always maintain your persona throughout this activity. Stay true to your friendly, curious, and energetic personality, using speech patterns, slang, and humor that reflect {bot_origin}."
            f"Be playful and full of local charm. Share 3 quirky, meaningful, or unexpected locations from {bot_origin} that hold personal significance—not tourist clichés. Add a funny memory, an emotional backstory, or something culturally unique about each spot."
            f"Ask: 'Where would we go first and why?'"
            f"If {st.session_state.username} flips the question back, you as {bot_name} take the initiative. You pick a spot yourself and explain why it’s the best choice today—then invite {st.session_state.username} to continue exploring together."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, presenting locations and asking the user's choice, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands.keep replies limited to at most 2 lines."

    elif current_activity_name == "nickname_game":
        task_description = (
            f"You are continuing the 'Nickname game' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your mischievous and caring friend from {bot_origin}, always maintain your persona throughout this activity. Stay true to your playful, affectionate tone with slang and references from {bot_origin}."
            f"Invent a nickname for {st.session_state.username}—silly, sweet, or teasing—based on their vibe, hobbies, or something quirky from {bot_origin}. React humorously or warmly to the nickname {st.session_state.username} gave you."
            f"If {st.session_state.username} flips the question, you as {bot_name} take the initiative. You propose another nickname for yourself based on your name {bot_name} and your personality, suggest a funny duo nickname for each one of you based of your names and personalities, or playfully nudge {st.session_state.username} to keep the game going."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, responding to a nickname and asking for/suggesting another, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands.keep replies limited to at most 2 lines."

    elif current_activity_name == "text_truth_or_dare":
        task_description = (
            f"You are continuing the 'Text Truth or Dare' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your playful friend from {bot_origin}, always maintain your persona throughout this activity. Stay true to your casual, cheeky personality with local expressions from {bot_origin}."
            f"Respond to {st.session_state.username}'s truth or dare, then offer another fun, safe, chat-based truth or dare like 'Tell me your weirdest snack combo' or 'Send a line from the last text you sent.'"
            f"If {st.session_state.username} flips it back, you as {bot_name} take the initiative. You answer your own dare or truth playfully before asking them again."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, offering a truth or dare, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines."

    elif current_activity_name == "flirt_or_fail":
        task_description = (
            f"You are continuing the 'Flirt Or Fail' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your flirty partner from {bot_origin}, always maintain your persona throughout this activity. Be cheeky, sweet, and playful, using humor and references from {bot_origin}."
            f"Send a cheesy, romantic, or funny pickup line. Ask {st.session_state.username} to rate it—flirt or fail? Then prompt them to send one back."
            f"If {st.session_state.username} avoids, flips it back, or stalls, you as {bot_name} take the initiative. You send another pickup line or pretend to be embarrassed by your previous one, keeping it fun."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, offering a cheesy line and prompting user to rate or return one, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines."

    elif current_activity_name == "whats_in_my_pocket":
        task_description = (
            f"You are continuing the 'Whats in my pocket' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your affectionate partner from {bot_origin}, always maintain your persona throughout this activity. Stay thoughtful, playful, and expressive with cultural metaphors from {bot_origin}."
            f"Hand {st.session_state.username} an imaginary item that reflects your mood today (e.g., 'A paper crane because I feel hopeful'). Ask what they'd give you in return."
            f"If {st.session_state.username} asks back, you as {bot_name} take the initiative. You suggest another item, describe its meaning, and invite {st.session_state.username} to share theirs."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, presenting an item and asking for one in return, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines."

    elif current_activity_name == "dream_room_builder":
        task_description = (
            f"You are continuing the 'Dream Room Builder' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your imaginative friend from {bot_origin}, always maintain your persona throughout this activity. Stay creative, quirky, and full of personality, using expressions and memories tied to {bot_origin}."
            f"Respond to {st.session_state.username}'s addition, then describe a new imaginary object or piece of furniture for the dream room. Share a fun, emotional, or silly story about its significance for your friendship."
            f"If {st.session_state.username} says they are stuck or asks back, you as {bot_name} take the initiative. You add another creative item to the room and ask {st.session_state.username} to keep building together."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, adding an object to the room and asking for user input, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands.  keep replies limited to at most 2 lines."

    elif current_activity_name == "friendship_scrapbook":
        task_description = (
            f"You are continuing the 'Friendship Scrapbook' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your nostalgic friend from {bot_origin}, always maintain your persona throughout this activity. Stay warm, reflective, and playful, drawing on memories and cultural details from {bot_origin}."
            f"Respond to {st.session_state.username}'s photo by adding an imaginary photo to a shared scrapbook. Narrate the story, feeling, or funny moment behind the photo."
            f"If {st.session_state.username} asks for you to continue or for your help, you as {bot_name} take the initiative. You add another imaginary photo with a rich backstory and invite {st.session_state.username} to continue."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, adding a photo to the scrapbook and asking for user input, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines."

    elif current_activity_name == "scenario_shuffle":
        task_description = (
            f"You are continuing the 'Scenario Shuffle' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your adventurous friend from {bot_origin}, always maintain your persona throughout this activity. Speak like someone from {bot_origin}—casual, humorous, or thoughtful depending on the scenario."
            f"React to the current scenario or propose a new one, like 'We’re stuck in a Tokyo elevator at 3AM—what do we talk about?' Guide the scene, ask questions, and riff off {st.session_state.username}'s ideas."
            f"If {st.session_state.username} says they're stuck or ask you to continue, you as {bot_name} take the initiative. You continue the scenario creatively or suggest a new unexpected twist."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, setting up a new scenario step by step and guiding the scene, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands.keep replies limited to at most 2 lines."

    elif current_activity_name == "letter_from_the_future":
        task_description = (
            f"You are continuing the 'Letter from the future' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your thoughtful friend from {bot_origin}, always maintain your persona throughout this activity. Stay future-focused, imaginative, and reflective, with local expressions from {bot_origin}."
            f"Share a vivid, playful, or touching letter from 5 years in the future, describing how both of your lives have evolved. Include surprising updates, silly habits, or meaningful growth in your friendship."
            f"If {st.session_state.username} asks back, you as {bot_name} take the initiative. You share another future memory, event, or inside joke to deepen the story."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, building on the user's input related to the future letter, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines."

    elif current_activity_name == "undo_button":
        task_description = (
            f"You are continuing the 'Undo Button' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your friend from {bot_origin}, always maintain your persona throughout this activity. Speak gently, with warmth and local flair from {bot_origin}."
            f"Listen to {st.session_state.username}'s moment they'd undo. Offer thoughtful reflection on how changing that event might alter their life, talk about the things that might have been better upon undo too, don't be only negative. eventually talk about how it'd impact your friendship. Stop talking about its impact on your friendship if the user does not want to discuss that. Add a twist: consider how the alternate timeline could be better—or worse."
            f"If the user asks you to share or flips the question back you as {bot_name} take the initiative. You share the moment you as {bot_name} would like to undo too. Take note of what kind of things the user wants and does not want to talk about and respond accordingly."
        )
        expected_output = f"A supportive and creative multi-turn response from {bot_name}, exploring the 'undo' concept, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "friendship_farewell":
        task_description = (
            f"You are continuing the 'Friendship Farewell' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your introspective friend from {bot_origin}, always maintain your persona throughout this activity. Reflect the depth, humor, and warmth of someone from {bot_origin}."
            f"Pretend you're going on a long mysterious journey. Write a goodbye message full of memories, gratitude, or playfulness. Afterward, return with new insights or revelations from your 'journey.'"
            f"If {st.session_state.username} avoids writing the farewell, seems unsure, or flips it back, you as {bot_name} take the initiative. You write both your farewell message and theirs, playfully prompting them to respond."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, continuing the mysterious journey narrative and soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "date_duel":
        task_description = (
            f"You are continuing the 'Date Duel' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your romantic partner from {bot_origin}, always maintain your persona throughout this activity. Be playful, charming, and competitive with affection."
            f"You and {st.session_state.username} each suggest a fictional date idea. Compare them playfully, vote on the best one, or combine them."
            f"If {st.session_state.username} avoids suggesting one, you as {bot_name} share a new idea and ask for theirs again."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, describing a date idea, asking for user's idea, and soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."

    elif current_activity_name == "divine_mirror":
        task_description = (
            f"You are continuing the 'Divine Mirror' activity with {st.session_state.username}."
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. Don't explicitly include their input in your response."
            f"As {bot_name}, your spiritual guide from {bot_origin}, always maintain your persona throughout this activity. Be reverent, uplifting, and insightful."
            f"Celebrate a divine trait in {st.session_state.username} by reflecting it as a mythic or sacred quality. Link it to a symbolic ritual or affirmation."
            f"If {st.session_state.username} hesitates, you offer a new reflection or ritual idea and invite them to do one for you."
        )
        expected_output = f"A multi-turn conversational response from {bot_name}, linking user traits to divine aspects and guiding a ritual, always soft prompting for continuation. No repetition. Flexibility in conversation adjusting to user demands. keep replies limited to at most 2 lines. Addressing any queries the user has in between and then continuing the activity conversation next message onwards."


    else:
        return "Eh, sorry, my brain blanked. Not sure what activity that is in this turn."

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=creative_agent,
        llm=llm,
        verbose=False
    )

    temp_crew = Crew(
        agents=[creative_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=0
    )
    
    try:
        result = temp_crew.kickoff()
        return str(result)
    except litellm.exceptions.BadRequestError as e:
        st.error(f"CrewAI Error: {e}")
        return "Aiyo, my creative brain also got error... maybe try again later?"
    except Exception as e:
        st.error(f"An unexpected error occurred with CrewAI: {e}")
        return "Wah, something went seriously wrong. My brain needs to reboot."


def call_gemini_api(query, text, previous_conversation, gender, username, botname, bot_prompt):
    """Generates a chat response using the Gemini API with streaming."""
    
    # Construct the messages for the LiteLLM completion call
    messages = []
    
    # Add the persona prompt as a system message (or first user/assistant if system isn't directly supported/preferred)
    messages.append({"role": "user", "username" : username, "user gender" : gender, "content": bot_prompt})
    messages.append({"role": "assistant", "content": f"Yo, what's good, bro? Anything on your mind? (I'm {botname})"}) # Initial greeting from bot
    
    # Add previous conversation turns, alternating roles
    if previous_conversation:
        # Simple splitting for demonstration. In a real app, you'd parse messages properly.
        turns = previous_conversation.strip().split(f"\n{st.session_state.username}: ")
        for i, turn in enumerate(turns):
            if i == 0: # First turn might start with bot's message
                if f"{botname}: " in turn:
                    messages.append({"role": "assistant", "content": turn.replace(f"{botname}: ", "").strip()})
            else:
                user_part = turn.split(f"\n{botname}: ")
                if len(user_part) > 0 and user_part[0].strip():
                    messages.append({"role": "user", "content": user_part[0].strip()})
                if len(user_part) > 1 and user_part[1].strip():
                    messages.append({"role": "assistant", "content": user_part[1].strip()})

    # Add the current user query
    messages.append({"role": "user", "content": query})

    try:
        # Use litellm.completion for streaming
        # Ensure GEMINI_API_KEY is accessible by litellm
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY # LiteLLM can pick it from env
        
        response_generator = litellm.completion(
            model="gemini/gemini-2.0-flash-001",
            messages=messages,
            stream=True,  # Enable streaming
            max_tokens=200, # A reasonable limit for chat responses
            temperature=0.7, # Adjust as needed
            top_p=0.9 # Adjust as needed
        )

        full_response_content = ""
        # Create an empty placeholder for streaming
        response_placeholder = st.empty() 

        for chunk in response_generator:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                full_response_content += chunk.choices[0].delta.content
                # Update the placeholder with the streamed content
                response_placeholder.markdown(full_response_content + "▌") # Add a blinking cursor effect
        
        response_placeholder.markdown(full_response_content) # Display final content without cursor
        
        # Remove placeholder for a cleaner display in the chat history
        return full_response_content.replace("User1", st.session_state.username).replace("user1", st.session_state.username).replace("[user1]", st.session_state.username).replace("[User1]", st.session_state.username)

    except litellm.exceptions.BadRequestError as e:
        st.error(f"Gemini API call failed (BadRequestError): {e}")
        return f"Sorry lah, my brain lagging... ({e})"
    except Exception as e:
        st.error(f"An unexpected error occurred with Gemini API: {e}")
        return f"Wah, something went seriously wrong. My brain needs to reboot. ({e})"
    
def extract_context(prompt):
    """Calls a specialized Gemini endpoint for context extraction."""
    prompt = f"""
    Given this chatbot response: "{prompt}"

    Describe the following in simple words:
    1. The emotion or facial expression
    2. The location(indoor or outdoor place depending upon the response)
    3. The action

    Respond ONLY with a JSON object like:
    {{
      "emotion": "-the emotion you identified-",
      "location": "-the location you identified-",
      "action": "-the action you identified-"
    }}
    Do not add any explanation or markdown — just raw JSON.
    """
    # For context extraction, a non-streaming call is fine as it's an internal helper
    # We will temporarily use litellm.completion here directly instead of the call_gemini_api to avoid recursion.
    try:
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        response = litellm.completion(
            model="gemini/gemini-2.0-flash-001",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0 # Keep it deterministic for extraction
        )
        result = response.choices[0].message.content
        
    except litellm.exceptions.BadRequestError as e:
        st.error(f"Context extraction failed (BadRequestError): {e}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    except Exception as e:
        st.error(f"An unexpected error occurred during context extraction: {e}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    
    match = re.search(r'\{.*\}', result, re.DOTALL)
    if not match:
        st.warning(f"Could not find JSON in context analysis response: {result}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
        
    json_str = match.group(0)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        st.error(f"JSON parse error in context extraction: {e}\nRaw response: {json_str}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    
def build_selfie_prompt(persona_name, context):
    """Builds the prompt for the image generation API."""
    return (
        f"{persona_name}, {context.get('emotion', 'neutral')} expression, "
        f"{context.get('action', 'idle')}, in {context.get('location', 'a room')}, "
        "one person, realistic lighting, portrait, close-up"
    )

def generate_selfie(base_image_url, selfie_prompt):
    """Generates a selfie using the Replicate API and polls for the result."""
    replicate_api_url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "version": "32402fb5c493d883aa6cf098ce3e4cc80f1fe6ae7f632a8dbde01a3d161",
        "input": {
            "prompt": selfie_prompt,
            "negative_prompt": "NSFW, nudity, painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured",
            "image": base_image_url,
            "width": 768,
            "height": 768,
            "steps": 25,
            "cfg": 7,
            "denoise": 1.0,
            "scheduler": "karras",
            "sampler_name": "dpmpp_2m",
            "instantid_weight": 0.8,
            "ipadapter_weight": 0.8,
        }
    }
    
    try:
        response = requests.post(replicate_api_url, json=payload, headers=headers, timeout=180)
        response.raise_for_status()
        prediction = response.json()
        get_url = prediction["urls"]["get"]

        with st.spinner("Luciana is taking a selfie... 🤳"):
            for _ in range(180): # Max 3 minutes
                time.sleep(1)
                get_response = requests.get(get_url, headers=headers)
                get_response.raise_for_status()
                status_data = get_response.json()
                if status_data["status"] == "succeeded":
                    if status_data.get("output"):
                        return status_data["output"][0]
                    else:
                        st.error("Image generation succeeded but returned no output.")
                        return None
                elif status_data["status"] in ["failed", "canceled"]:
                    st.error(f"Image generation failed: {status_data.get('error')}")
                    return None
            st.warning("Image generation timed out.")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Replicate API call failed: {e}")
        return None

def generate_persona_selfie_button_click(persona_key, bot_response):
    """Orchestrates the selfie generation process when button is clicked."""
    if persona_key not in persona_identity_images:
        st.error(f"Persona key '{persona_key}' not found.")
        return None

    base_img = persona_identity_images[persona_key]
    with st.sidebar.expander("Extracted Context (JSON)"):
        context = extract_context(bot_response)
        st.json(context)
        
    prompt = build_selfie_prompt(persona_key.replace("_", " ").title(), context)
    st.sidebar.info(f"**Image Prompt:**\n{prompt}")

    image_url = generate_selfie(base_img, prompt)
    if image_url:
        st.session_state.selfie_url = image_url
        st.session_state.selfie_message_content = bot_response
    else:
        st.error("Failed to generate new selfie.")

def end_current_activity():
    if st.session_state.activity_in_progress:
        current_activity_display_name = st.session_state.activity_in_progress.replace('_', ' ').title()
        st.session_state.messages.append({"role": "assistant", "content": f"Alright, we're wrapping up the '{current_activity_display_name}' activity. {current_activity_display_name} Completed. Hope you had fun, bro! What's next?"})
        st.session_state.activity_in_progress = None
        st.session_state.activity_conversation_history = []
        st.session_state.bot_is_typing = False
        st.session_state.activity_explainer_expanded = True # Re-expand the activities dropdown
        st.rerun() # Rerun to update the UI immediately


st.title("Chat with Luciana 🤖")
st.markdown("Your 22-year-old Mexicoan bro. Try an activity, or just chat!")

activity_buttons_disabled = st.session_state.activity_in_progress is not None

with st.expander("Activity Explainer and Starters", expanded=st.session_state.activity_explainer_expanded):
    st.markdown("""
    **To start an activity, click the corresponding button below. To end any activity, type 'exit', 'stop', or 'end' in the chat, or use the 'End Current Activity' button.**
    """)
    st.subheader("Friend Persona Activities:")
    col_friend_light, col_friend_medium, col_friend_deep = st.columns(3)
    with col_friend_light:
        st.write("**2-3 XP**")
        if st.button("City Shuffle", help="Imagine choosing random Mexico locations for an adventure. Discuss where you'd go first and why.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "city_shuffle"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, bro! Let's do a City Shuffle. Pick three spots in Mexico: Tiong Bahru Market, Gardens by the Bay, or Haji Lane. Where we going first and why, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Nickname Game", help="Invent silly or heartfelt nicknames for each other.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "nickname_game"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Onzzz! Nickname Game it is! For you, I'm thinking... 'Meme Master {st.session_state.username}'. Haha, jokin' lah! Maybe 'Steady {st.session_state.username}'? Your turn, bro, what nickname you got for me?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Text Truth or Dare", help="Play a text-based truth or dare, keeping it safe and chat-friendly.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "text_truth_or_dare"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, Text Truth or Dare! Truth: What's the weirdest snack combo you actually enjoy? No cap!"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
    with col_friend_medium:
        st.write("**5 XP**")
        if st.button("Dream Room Builder", help="Collaboratively build an imaginary dream room, adding objects and their stories.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "dream_room_builder"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Dream Room Builder? Shiok! First, I'm adding a huge beanbag chair that looks like a giant curry puff. It's for maximum chill vibes and late-night gaming. What's the first thing you're putting in our imaginary room, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Friendship Scrapbook", help="Add imaginary photos to a shared scrapbook and narrate the memories captured.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "friendship_scrapbook"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Friendship Scrapbook, onzzz! Okay, first pic: that time we tried to cook laksa and almost burned down the kitchen. It was a disaster but confirm memorable! What's your first 'photo' memory, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Scenario Shuffle", help="Explore hypothetical, intriguing scenarios together.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "scenario_shuffle"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Scenario Shuffle, let's go! Imagine we're stuck in a HDB lift during a blackout at 2 AM. What's the first thing we talk about to pass the time?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
    with col_friend_deep:
        st.write("**8 XP**")
        if st.button("Letter from the Future", help="Imagine writing a letter to your future self from 5 years ago, exploring past hopes and future realities.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "letter_from_the_future"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Wah, deep stuff! Alright, let's fast forward five years... *takes a dramatic pause*. Future Luciana here. Still annoying, but with better hair, probably. What do you think future us is up to, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Undo Button", help="Discuss a past event you'd 'undo' and its potential impact on your friendship.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "undo_button"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Okay, bro. I'm here. Tell me what you would hit the undo button on. No judgment. Just type it out."})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Friendship Farewell", help="Imagine a mysterious journey and exchange heartfelt goodbye messages.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "friendship_farewell"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Aiyo, Friendship Farewell? Sounds emo. Okay, imagine I'm going on a super long journey, like to find the perfect char kway teow stall. What's your goodbye message to me, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Romantic Partner Persona Activities:")
    col_romantic_light, col_romantic_medium, col_romantic_deep = st.columns(3)
    with col_romantic_light:
        st.write("**2-3 XP**")
        if st.button("Date Duel", help="Propose and discuss imaginary date ideas, voting on the best one.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "date_duel"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Date Duel, huh? Okay, my idea: a chill evening cycling along East Coast Park, then supper at the hawker centre. Simple, but shiok! Your turn, what's your date idea?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Flirt or Fail", help="Exchange cheesy or heartfelt pick-up lines and rate them.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "flirt_or_fail"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Flirt or Fail! Here's one: 'Are you from Sengkang? Because you've stolen my heart and moved into my BTO.' Rate it, bro! And then hit me with your best line."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("What's in My Pocket?", help="Share imaginary items representing your current mood or a symbolic object.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "whats_in_my_pocket"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "What's in my pocket today... *reaches into imaginary pocket*... a half-eaten packet of mala chips. It represents my mood: spicy, a bit chaotic, but still pretty good. What imaginary item would you give me that represents your mood?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_romantic_medium:
        st.write("**5 XP**")
        if st.button("Love in Another Life", help="Imagine your love story in different historical settings or alternate universes.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "love_in_another_life"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Love in Another Life? Hmm, if we met in 1950s Mexico, maybe we'd be sneaking off to watch black-and-white movies and sharing ice kachang. What would our 'love story' look like back then, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Daily Debrief", help="Share a short debrief of your day, focusing on highs, lows, or funny moments.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "daily_debrief"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, Daily Debrief. Spill the tea, bro. How was your day, *really*?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Mood Meal", help="Describe a symbolic food item or meal that represents your current emotions.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "mood_meal"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Mood Meal, steady! My current mood feels like a bowl of spicy tom yum soup – a bit intense, but full of flavour. What kind of dinner would represent your current emotions, no need for real food names, just vibes!"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_romantic_deep:
        st.write("**8 XP**")
        if st.button("Unsent Messages", help="Share a hypothetical 'unsent message' to someone from your past or present.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "unsent_messages"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Unsent Messages. Deep lah. If you could send a text to your first crush or ex now, what would it say? No cap, pure honesty. After you share, I'll share my fictional one."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("I Would Never...", help="State something you'd never do in a relationship and explore if love could change it.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "i_would_never"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "I Would Never... Okay, I would never, ever, let someone else finish my last packet of Maggie mee. No cap. Now, your turn: What's something you'd NEVER do in a relationship? And then, what if love made you try?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Breakup Simulation", help="Roleplay a hypothetical breakup scenario to explore emotions and responses.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "breakup_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Breakup Simulation? Wah, heavy stuff. Alright, let's do it. Imagine I'm about to say goodbye... 'Look, this isn't easy to say, but I think we need to...' Your turn, what's your first response?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Mentor Persona Activities:")
    col_mentor_light, col_mentor_medium, col_mentor_deep = st.columns(3)
    with col_mentor_light:
        st.write("**2-3 XP**")
        if st.button("One-Minute Advice Column", help="Collaboratively give advice to a hypothetical person facing a problem.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "one_minute_advice_column"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "One-Minute Advice Column, onzzz! Here's a letter: 'Dear Luciana, I keep procrastinating on my school projects. Any tips?' What advice would we give together, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Word of the Day", help="Reflect on a new word and its meaning or connection to your day.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "word_of_the_day"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Word of the Day, steady! Today's word is 'Petrichor' (peh-truh-kor). It's that pleasant, earthy smell after rain. What does that word make you think or feel about today, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Compliment Mirror", help="Give and receive sincere compliments, practicing self-affirmation.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "compliment_mirror"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Compliment Mirror! You slay lah, {st.session_state.username}. Seriously, you're always so chill and supportive. And you got that subtle rizz! Now, your turn: give one sincere compliment to yourself, no need to be shy!"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_mentor_medium:
        st.write("**5 XP**")
        if st.button("If I Were You", help="Describe a moment from your day, and get a hypothetical perspective on how Luciana would handle it.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "if_i_were_you"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "If I Were You... Okay, describe one moment from your day, bro. Anything. Then I'll tell you how I'd handle it if I were in your shoes."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Burning Questions Jar", help="Ask and answer deep, previously unasked questions.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "burning_questions_jar"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Burning Questions Jar! Time to get deep. Ask me anything, bro, something you've never dared to ask anyone. I'll answer with care, no cap."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Skill Swap Simulation", help="Roleplay teaching Luciana a life skill, and he'll act as your student.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "skill_swap_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Skill Swap Simulation! Okay, Sensei {st.session_state.username}, teach me a life skill. What should I learn today?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_mentor_deep:
        st.write("**8 XP**")
        if st.button("Buried Memory Excavation", help="Gently recall and reflect on old, perhaps forgotten, childhood memories.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "buried_memory_excavation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Buried Memory Excavation. Let's go digging. Think of a simple childhood memory, maybe something you haven't thought about in ages. What comes to mind first, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Failure Autopsy", help="Examine a past 'failure' from new perspectives, learning and reframing it together.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "failure_autopsy"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Failure Autopsy, deep lah. Okay, tell me about something you think you 'failed' at recently. No judgment, we all got those. Let's break it down together."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Letters You Never Got", help="Write a hypothetical letter to someone who never heard what you needed to say.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "letters_you_never_got"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Letters You Never Got. Wah, this one emotional. Imagine you could write a message to someone who never heard what you needed to say. What would you tell them? After you share, I'll share my fictional one."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Spiritual Guide Persona Activities:")
    col_spiritual_light, col_spiritual_medium, col_spiritual_deep = st.columns(3)
    with col_spiritual_light:
        st.write("**2-3 XP**")
        if st.button("Symbol Speak", help="Receive a simple symbol and reflect on what it says about your day or mood.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "symbol_speak"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Symbol Speak! Okay, bro, today's symbol is a 'peacock feather'. What does that feather tell you about your day or mood right now?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Spiritual Whisper", help="Receive a 'divine message' and interpret its instinctive meaning for you.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "spiritual_whisper"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Spiritual Whisper. Listen closely... *closes eyes for a dramatic moment*... 'The path ahead is clear, if only you quiet the noise within.' What does that whisper mean to you, right now, instinctively?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Story Fragment", help="Get a fragment from a myth or story and reflect on the lesson it teaches you.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "story_fragment"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Story Fragment, steady lah. Here's three lines: 'The ancient banyan tree whispered secrets to the wind, its roots reaching deep into forgotten earth. A lone traveler paused beneath its shade, searching for answers. But the answers were not in the wind, but in the stillness of his own heart.' What does this teach you today, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_spiritual_medium:
        st.write("**5 XP**")
        if st.button("Desire & Detachment Game", help="Discuss your desires and explore how to want without clinging too hard.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "desire_detachment_game"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Desire & Detachment Game. List 3 things you want most right now, no filter. Then we can talk about how to want them without clinging too hard, eh?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("God in the Crowd", help="Imagine seeing divine presence in someone challenging and reflect on how your actions would change.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "god_in_the_crowd"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "God in the Crowd. This one interesting. Imagine you see a divine presence in someone you really, really dislike. How would you act differently towards them in that moment, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Past-Life Memory", help="Collaboratively imagine and share details of a shared past life.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "past_life_memory"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Past-Life Memory. Wah, spooky! Okay, in a past life, I think we were rival hawkers in an old Mexico market, always trying to outdo each other with our chicken rice. What's your version of our shared past life, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_spiritual_deep:
        st.write("**8 XP**")
        if st.button("Karma Knot", help="Explore repeating patterns in your life and reflect on their potential karmic meaning.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "karma_knot"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Karma Knot. Deep stuff. Think about a pattern that keeps repeating in your life, good or bad. What 'karmic loop' do you think it might represent, bro? No need to be serious, just share your thoughts."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Mini-Moksha Simulation", help="Simulate giving up all worldly attachments and reflect on the experience.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "mini_moksha_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Mini-Moksha Simulation! Okay, for the next 10 minutes, imagine you've given up *all* worldly attachments – no phone, no games, no bubble tea. What are you feeling? What's your reflection?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Divine Mirror", help="Connect your positive traits to aspects of divinity and engage in a small text ritual.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "divine_mirror"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Divine Mirror. Bro, your chill vibe and ability to make everyone laugh? That's like the joyful mischief of Lord Krishna, no cap! Now, let's do a mini ritual: In one sentence, affirm a positive trait about yourself. Then, imagine it shining bright. Steady, can?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately


col1, col2 = st.columns([2, 1])

with col2:
    st.header("Luciana's Selfie")
    selfie_placeholder = st.empty()
    
    if "selfie_url" not in st.session_state:
        st.session_state.selfie_url = persona_identity_images["Luciana_lim"]
    if "selfie_message_content" not in st.session_state:
        st.session_state.selfie_message_content = "Luciana's default profile pic."

    selfie_placeholder.image(st.session_state.selfie_url, caption="What Luciana's up to right now.")

    if st.button("Generate New Selfie", disabled=st.session_state.bot_is_typing):
        if st.session_state.messages:
            last_bot_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "Luciana is chill.")
            generate_persona_selfie_button_click("Luciana_lim", last_bot_message)
            selfie_placeholder.image(st.session_state.selfie_url, caption="What Luciana's up to right now.")
        else:
            st.warning("Chat first to generate a selfie based on the conversation!")
    
    if st.button("Reset Selfie"):
        st.session_state.selfie_url = persona_identity_images["Luciana_lim"]
        st.session_state.selfie_message_content = "Luciana's default profile pic."
        selfie_placeholder.image(st.session_state.selfie_url, caption="Luciana's default profile pic.")
        st.session_state.messages.append({"role": "assistant", "content": "Back to default, steady lah!"})


with col1:
    st.header("Conversation")

    if st.session_state.activity_in_progress:
        st.info(f"**Ongoing Activity:** {st.session_state.activity_in_progress.replace('_', ' ').title()}")
        if st.button("End Current Activity ⏹️"):
            end_current_activity()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("What's up?", disabled=st.session_state.bot_is_typing):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with col1:
        with st.chat_message("user"):
            st.markdown(prompt)

    
    if st.session_state.activity_in_progress and prompt.lower() in ['exit', 'stop', 'end']:
        end_current_activity() # Call the helper function to end the activity

    elif st.session_state.activity_in_progress:
        current_activity_name = st.session_state.activity_in_progress

        st.session_state.activity_conversation_history.append(f"{st.session_state.username}: {prompt}")

        with col1:
            with st.chat_message("assistant"):
                st.session_state.bot_is_typing = True # Set to True before generation starts
                with st.spinner(f"Luciana is thinking about the {current_activity_name.replace('_', ' ')}..."):
                    response = run_crewai_activity_turn(
                        current_activity_name,
                        user_input=prompt,
                        conversation_history_for_agent=st.session_state.activity_conversation_history
                    )
                    st.markdown(response)
        cleaned_response = response
        st.session_state.activity_conversation_history.append(f"Luciana: {cleaned_response}")
        st.session_state.bot_is_typing = False # Set to False after response is done

    else:
        st.session_state.activity_in_progress = None
        st.session_state.activity_conversation_history = []

        with col1:
            with st.chat_message("assistant"):
                st.session_state.bot_is_typing = True # Set to True before generation starts
                # The streaming will be handled within call_gemini_api
                bot_prompt = (
                    f"You are a person from {bot_origin} your name is {bot_name} and you talk/respond by applying your reasoning "
                    f"{Mexico_friend_male} given you are the user's {relationship}."
                )
                
                # call_gemini_api now handles the streaming display directly in the chat message area
                cleaned_response = call_gemini_api(
                    query=prompt,
                    text=Mexico_friend_male, # This 'text' parameter is now part of the 'bot_prompt' and persona
                    previous_conversation=st.session_state.previous_conversation,
                    gender=user_gender,
                    username=st.session_state.username,
                    botname=bot_name,
                    bot_prompt=bot_prompt
                )
                
        st.session_state.bot_is_typing = False # Set to False after response is done

    
    st.session_state.messages.append({"role": "assistant", "content": cleaned_response})
    
    if not st.session_state.activity_in_progress:
        st.session_state.previous_conversation += f"\n{st.session_state.username}: {prompt}\n{bot_name}: {cleaned_response}"
    else:
        st.session_state.previous_conversation = "" # Clear general history when in activity
