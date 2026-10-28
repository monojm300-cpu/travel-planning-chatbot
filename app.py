import re
from datetime import date, timedelta

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
        "food": "Goan cuisine and seafood",
        "color": "0ea5e9",
        "tagline": "Beaches, sunsets and seafood"
    },
    "Manali": {
        "budget": 15000,
        "transport": ["Bus", "Train + Taxi", "Flight + Taxi"],
        "hotel": "Budget hotels and mountain homestays",
        "places": ["Hadimba Temple", "Solang Valley", "Mall Road", "Old Manali"],
        "food": "Himachali and North Indian food",
        "color": "6366f1",
        "tagline": "Snow-capped mountains and valleys"
    },
    "Jaipur": {
        "budget": 9000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Budget hotels and heritage guesthouses",
        "places": ["Hawa Mahal", "Amber Fort", "City Palace", "Jantar Mantar"],
        "food": "Rajasthani thali and local street food",
        "color": "f97316",
        "tagline": "Forts, palaces and pink-city charm"
    },
    "Kerala": {
        "budget": 16000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Hotels, homestays and resorts",
        "places": ["Alleppey backwaters", "Munnar tea gardens", "Fort Kochi", "Spice markets"],
        "food": "Traditional Kerala cuisine",
        "color": "16a34a",
        "tagline": "Backwaters and tea-garden greens"
    },
    "Ooty": {
        "budget": 8000,
        "transport": ["Bus", "Train + Taxi", "Car"],
        "hotel": "Budget hotels and hill-view homestays",
        "places": ["Botanical Garden", "Ooty Lake", "Doddabetta Peak", "Nilgiri Mountain Railway"],
        "food": "South Indian food and local chocolates",
        "color": "0d9488",
        "tagline": "Hill-station views and toy trains"
    },
    "Bengaluru": {
        "budget": 7000,
        "transport": ["Bus", "Train", "Flight"],
        "hotel": "Budget hotels and city guesthouses",
        "places": ["Lalbagh Garden", "Cubbon Park", "Bengaluru Palace", "Commercial Street"],
        "food": "South Indian cuisine and local cafes",
        "color": "a855f7",
        "tagline": "Gardens, cafes and city life"
    }
}


def destination_image(name, width=400, height=220):
    """Return a lightweight, always-available placeholder banner for a destination."""
    color = DESTINATIONS[name]["color"]
    label = name.replace(" ", "+")
    return f"https://placehold.co/{width}x{height}/{color}/ffffff?text={label}"


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
            "You can also tell me your budget, or use the quick-fill "
            "form in the sidebar instead of typing."
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
            "budget for destination suggestions, or use the sidebar form."
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


def push_assistant_message(content):
    st.session_state.messages.append({"role": "assistant", "content": content})


# ---------------- STREAMLIT USER INTERFACE ----------------

st.title("✈️ Travel Planning Chatbot")
st.caption("CA3 Project | Intent detection | Entity extraction | Multi-turn conversation")

with st.expander("How to use this chatbot"):
    st.write(
        "Tell the chatbot your destination, budget, dates, trip duration, "
        "transport and hotel preference by typing in the chat box, or fill "
        "in the quick-fill form in the sidebar. Type 'show plan' to review "
        "your details or 'reset' to start over."
    )
    st.info(
        "This project uses sample destinations and illustrative estimates. "
        "It does not check live prices or make bookings."
    )

# ---- Destination gallery (dynamic banner images) ----
if st.session_state.trip["Destination"]:
    chosen = st.session_state.trip["Destination"]
    st.image(
        destination_image(chosen, width=900, height=260),
        caption=f"{chosen} — {DESTINATIONS[chosen]['tagline']}",
        use_container_width=True
    )
else:
    st.write("#### Explore destinations")
    gallery_cols = st.columns(3)
    for index, name in enumerate(DESTINATIONS):
        with gallery_cols[index % 3]:
            st.image(destination_image(name), use_container_width=True)
            st.caption(f"**{name}** — {DESTINATIONS[name]['tagline']}")

st.divider()

# ---- Chat history ----
for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

prompt = st.chat_input("Type your travel question...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    answer = chatbot_response(prompt)
    push_assistant_message(answer)

    with st.chat_message("assistant"):
        st.markdown(answer)

# ---------------- SIDEBAR: QUICK-FILL FORM + TRIP SUMMARY ----------------

with st.sidebar:
    st.header("Quick Trip Form")
    st.caption("Prefer clicking over typing? Fill this in and apply it to the chat.")

    with st.form("quick_trip_form"):
        destination_choice = st.selectbox(
            "Destination",
            options=["-- Select --"] + list(DESTINATIONS.keys()),
            index=0
        )

        budget_choice = st.number_input(
            "Budget per person (₹)",
            min_value=0,
            max_value=200000,
            step=500,
            value=int(st.session_state.trip["Budget"] or 0)
        )

        date_choice = st.date_input(
            "Travel date",
            value=date.today() + timedelta(days=7),
            min_value=date.today()
        )

        duration_choice = st.slider(
            "Duration (days)",
            min_value=1,
            max_value=14,
            value=int(st.session_state.trip["Duration"] or 3)
        )

        transport_choice = st.selectbox(
            "Transport",
            options=["Bus", "Train", "Flight", "Car", "Bike", "Taxi"]
        )

        hotel_choice = st.selectbox(
            "Accommodation",
            options=["Budget", "Luxury", "Resort / Homestay / Hostel", "No preference"]
        )

        submitted = st.form_submit_button("Apply to trip", use_container_width=True)

        if submitted:
            trip = st.session_state.trip
            if destination_choice != "-- Select --":
                trip["Destination"] = destination_choice
            if budget_choice > 0:
                trip["Budget"] = int(budget_choice)
            trip["Date"] = date_choice.strftime("%B %d, %Y")
            trip["Duration"] = duration_choice
            trip["Transport Type"] = transport_choice
            trip["Hotel"] = hotel_choice

            push_assistant_message(
                "Got it — I've updated your trip details from the quick-fill form. "
                "Type **show plan** to see the full itinerary, or keep chatting to change anything."
            )
            st.rerun()

    st.divider()

    st.header("Your Trip Details")
    trip = st.session_state.trip
    filled = sum(1 for value in trip.values() if value is not None)
    st.progress(filled / len(trip), text=f"{filled} of {len(trip)} details filled")

    for key, value in trip.items():
        st.write(f"**{key}:** {value if value is not None else 'Not provided'}")

    if st.button("Reset conversation", use_container_width=True):
        st.session_state.trip = new_trip()
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! Where would you like to travel? You can choose Goa, Manali, Jaipur, Kerala, Ooty or Bengaluru."
        }]
        st.rerun()
