
import re
import streamlit as st

st.set_page_config(
    page_title="Travel Planning Chatbot",
    page_icon="✈️",
    layout="centered"
)

# ---------------- SAMPLE DESTINATION DATABASE ----------------

DESTINATIONS = {
    "Goa": {
        "budget": 12000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Budget hotels and beachside stays",
        "places": ["Baga Beach", "Fort Aguada", "Basilica of Bom Jesus", "Local markets"],
        "food": "Goan cuisine and seafood"
    },
    "Manali": {
        "budget": 15000,
        "transport": ["Bus", "Train + Taxi", "Flight + Taxi"],
        "hotel": "Budget hotels and mountain homestays",
        "places": ["Hadimba Temple", "Solang Valley", "Mall Road", "Old Manali"],
        "food": "Himachali and North Indian food"
    },
    "Jaipur": {
        "budget": 9000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Budget hotels and heritage guesthouses",
        "places": ["Hawa Mahal", "Amber Fort", "City Palace", "Jantar Mantar"],
        "food": "Rajasthani thali and local street food"
    },
    "Kerala": {
        "budget": 16000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Hotels, homestays and resorts",
        "places": ["Alleppey backwaters", "Munnar tea gardens", "Fort Kochi", "Spice markets"],
        "food": "Traditional Kerala cuisine"
    },
    "Ooty": {
        "budget": 8000,
        "transport": ["Bus", "Train + Taxi", "Car"],
        "hotel": "Budget hotels and hill-view homestays",
        "places": ["Botanical Garden", "Ooty Lake", "Doddabetta Peak", "Nilgiri Mountain Railway"],
        "food": "South Indian food and local chocolates"
    },
    "Bengaluru": {
        "budget": 7000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Budget hotels and city guesthouses",
        "places": ["Lalbagh Garden", "Cubbon Park", "Bengaluru Palace", "Commercial Street"],
        "food": "South Indian cuisine and local cafes"
    }
}

# ---------------- INTENT DETECTION ----------------

def detect_intent(message):
    text = message.lower().strip()

    if re.search(r"\b(bye|goodbye|exit|quit|done)\b", text):
        return "GOODBYE"
    if re.search(r"\b(hello|hi|hey|greetings)\b", text):
        return "GREETING"
    if re.search(r"\b(itinerary|trip plan|travel plan|places to visit|sightseeing)\b", text):
        return "ITINERARY"
    if re.search(r"\b(hotel|stay|accommodation|resort|homestay|hostel)\b", text):
        return "HOTEL"
    if re.search(r"\b(train|bus|flight|plane|transport|taxi|cab|car|bike)\b", text):
        return "TRANSPORT"
    if re.search(r"\b(budget|cost|price|cheap|afford|rupees|inr|under|below|within)\b", text):
        return "BUDGET"
    if re.search(r"\b(date|when|tomorrow|weekend|january|february|march|april|may|june|july|august|september|october|november|december)\b", text):
        return "DATES"
    if re.search(r"\b(destination|where|visit|travel to|trip to|holiday in|vacation in)\b", text):
        return "DESTINATION"

    return "UNKNOWN"


# ---------------- ENTITY EXTRACTION ----------------

def extract_entities(message):
    text = message.strip()
    lower = text.lower()
    entities = {}

    # Destination
    for place in DESTINATIONS:
        if re.search(r"\b" + re.escape(place.lower()) + r"\b", lower):
            entities["Destination"] = place
            break

    # Budget: ₹15000, Rs 15000, 15k, 15 thousand
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*(k|thousand)?",
        r"\b([\d,]+)\s*(k|thousand)\b",
        r"\b(?:budget|under|below|within|around|maximum|spend|cost)\s*(?:of\s*)?(?:₹|rs\.?|inr)?\s*([\d,]+)"
    ]

    for index, pattern in enumerate(patterns):
        match = re.search(pattern, lower)
        if match:
            amount = int(match.group(1).replace(",", ""))
            if index < 2 and len(match.groups()) > 1 and match.group(2):
                amount *= 1000
            if amount >= 1000:
                entities["Budget"] = amount
                break

    # Duration
    match = re.search(r"\b(\d+)\s*(days?|nights?|weeks?)\b", lower)
    if match:
        duration = int(match.group(1))
        if match.group(2).startswith("week"):
            duration *= 7
        entities["Duration"] = min(duration, 14)

    # Date or travel period
    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,?\s+\d{4})?\b",
        r"\b(?:today|tomorrow|this weekend|next weekend|next week|next month|this month)\b"
    ]

    for pattern in date_patterns:
        match = re.search(pattern, lower)
        if match:
            entities["Date"] = match.group(0)
            break

    # Transport type
    transport_keywords = {
        "Flight": ["flight", "plane"],
        "Train": ["train", "railway"],
        "Bus": ["bus", "coach"],
        "Car": ["car", "driving"],
        "Bike": ["bike", "motorcycle"],
        "Taxi": ["taxi", "cab"]
    }

    for transport, keywords in transport_keywords.items():
        if any(word in lower for word in keywords):
            entities["Transport Type"] = transport
            break

    # Hotel preference
    if re.search(r"\b(budget|cheap|affordable)\s+(hotel|stay)\b", lower):
        entities["Hotel"] = "Budget"
    elif re.search(r"\b(luxury|premium|five star|5 star)\b", lower):
        entities["Hotel"] = "Luxury"
    elif re.search(r"\b(resort|homestay|hostel)\b", lower):
        entities["Hotel"] = "Resort / Homestay / Hostel"
    elif re.search(r"\b(no preference|any hotel|any stay)\b", lower):
        entities["Hotel"] = "No preference"

    return entities


# ---------------- TRAVEL RECOMMENDATIONS ----------------

def recommend_destinations(budget):
    matches = [
        (name, data)
        for name, data in DESTINATIONS.items()
        if data["budget"] <= budget
    ]
    matches.sort(key=lambda item: item[1]["budget"])
    return matches[:4]


def create_itinerary(destination, duration):
    places = DESTINATIONS[destination]["places"]
    lines = []

    for day in range(1, duration + 1):
        first = ((day - 1) * 2) % len(places)
        second = (first + 1) % len(places)
        lines.append(
            f"**Day {day}:** Visit {places[first]} and {places[second]}."
        )

    return "\n\n".join(lines)


# ---------------- CHATBOT CONTEXT ----------------

def new_trip():
    return {
        "Destination": None,
        "Budget": None,
        "Date": None,
        "Duration": None,
        "Transport Type": None,
        "Hotel": None
    }


if "trip" not in st.session_state:
    st.session_state.trip = new_trip()

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            "Hello! Welcome to the Travel Planning Chatbot. "
            "Where would you like to travel? You can choose Goa, "
            "Manali, Jaipur, Kerala, Ooty or Bengaluru. "
            "You can also tell me your budget."
        )
    }]


def chatbot_response(message):
    trip = st.session_state.trip
    text = message.strip()
    lower = text.lower()
    intent = detect_intent(text)
    entities = extract_entities(text)

    if lower in ["reset", "restart", "start over"]:
        st.session_state.trip = new_trip()
        return "Let's start again! Where would you like to travel?"

    if lower in ["show plan", "my plan", "show details"]:
        return "\n".join(
            f"- **{key}:** {value if value is not None else 'Not provided'}"
            for key, value in trip.items()
        )

    if intent == "GOODBYE":
        return "Thank you for using the Travel Planning Chatbot. Have a wonderful trip!"

    if intent == "GREETING":
        return "Hello! Tell me your destination or budget, and I'll help plan your trip."

    # Allow the user to skip an unknown preference.
    if lower in ["skip date", "skip the date"]:
        trip["Date"] = "Not decided"
    elif lower in ["skip duration", "skip the duration"]:
        trip["Duration"] = 3
    elif lower in ["skip transport", "skip the transport"]:
        trip["Transport Type"] = "Not decided"
    elif lower in ["skip hotel", "skip accommodation", "no preference", "any"]:
        trip["Hotel"] = "No preference"

    # Save extracted entities between turns.
    for key, value in entities.items():
        if key in trip:
            trip[key] = value

    # Budget-based recommendations
    if trip["Budget"] and not trip["Destination"] and (
        intent == "BUDGET" or "recommend" in lower or "suggest" in lower
    ):
        options = recommend_destinations(trip["Budget"])
        if not options:
            return (
                "Your budget is below the sample trip estimates. "
                "Consider a shorter trip or increasing your budget."
            )

        result = ["Destinations within your budget (approximate cost per person):"]
        for name, data in options:
            result.append(f"- **{name}:** ₹{data['budget']:,}")
        result.append("Which destination would you like to choose?")
        return "\n".join(result)

    if not trip["Destination"]:
        return (
            "Which destination are you interested in? Choose Goa, Manali, "
            "Jaipur, Kerala, Ooty or Bengaluru. You can also share your "
            "budget for destination suggestions."
        )

    destination = trip["Destination"]
    data = DESTINATIONS[destination]

    if trip["Budget"] is None:
        return (
            f"Nice choice! The sample estimate for {destination} is "
            f"around ₹{data['budget']:,} per person. What is your total budget?"
        )

    if trip["Date"] is None:
        return "When are you planning to travel? For example, October 20 or next weekend. Type **skip date** if undecided."

    if trip["Duration"] is None:
        return "How many days will you stay? For example, 3 days or 1 week. Type **skip duration** if unsure."

    if trip["Transport Type"] is None:
        return "Which transport do you prefer: bus, train, flight, car, bike or taxi? Type **skip transport** if undecided."

    if trip["Hotel"] is None:
        return "What accommodation do you prefer: budget hotel, luxury hotel, resort, homestay, or no preference?"

    budget_note = ""
    if trip["Budget"] < data["budget"]:
        budget_note = (
            "\n\n**Budget note:** Your budget is below the sample estimate. "
            "Consider a shorter stay or a lower-cost destination."
        )

    return (
        "## Your Travel Plan\n\n"
        f"- **Destination:** {destination}\n"
        f"- **Budget:** ₹{trip['Budget']:,}\n"
        f"- **Travel date:** {trip['Date']}\n"
        f"- **Duration:** {trip['Duration']} days\n"
        f"- **Transport:** {trip['Transport Type']}\n"
        f"- **Accommodation:** {trip['Hotel']}\n"
        f"- **Sample estimate:** ₹{data['budget']:,} per person\n\n"
        "### Suggested itinerary\n\n"
        + create_itinerary(destination, trip["Duration"])
        + f"\n\n**Food suggestion:** {data['food']}\n\n"
        f"**Accommodation guidance:** {data['hotel']}\n\n"
        "_These are illustrative estimates, not live prices or bookings. "
        "Check current fares and availability before travelling._"
        + budget_note
        + "\n\nType **show plan** to review details or **reset** to start again."
    )


# ---------------- STREAMLIT USER INTERFACE ----------------

st.title("Travel Planning Chatbot")
st.caption("CA3 Project | Intent detection | Entity extraction | Multi-turn conversation")

with st.expander("How to use this chatbot"):
    st.write(
        "Tell the chatbot your destination, budget, dates, trip duration, "
        "transport and hotel preference. Type 'show plan' to review your "
        "details or 'reset' to start over."
    )
    st.info(
        "This project uses sample destinations and illustrative estimates. "
        "It does not check live prices or make bookings."
    )

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

prompt = st.chat_input("Type your travel question...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    answer = chatbot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.markdown(answer)

with st.sidebar:
    st.header("Your Trip Details")
    for key, value in st.session_state.trip.items():
        st.write(f"**{key}:** {value if value is not None else 'Not provided'}")

    if st.button("Reset conversation", use_container_width=True):
        st.session_state.trip = new_trip()
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! Where would you like to travel? You can choose Goa, Manali, Jaipur, Kerala, Ooty or Bengaluru."
        }]
        st.rerun()
