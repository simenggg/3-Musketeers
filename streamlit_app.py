"""Streamlit UI for RecipeBot - Simple prototype interface."""

import streamlit as st
import threading
import time
import pandas as pd
from datetime import datetime, date
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

from src.server.mcp_server import start_advanced_fridge_server
from src.services.fridge_service import FridgeService
from src.services.recipe_service import RecipeService
from src.services.memory_service import MemoryService
from src.agents.recipe_agent import RecipeAgent
from src.utils.logging_config import disable_logging
from src.config.settings import settings


def init_services():
    """Initialize services and agent."""
    if 'initialized' not in st.session_state:
        disable_logging()
        
        # Initialize services
        st.session_state.fridge_service = FridgeService()
        st.session_state.recipe_service = RecipeService()
        st.session_state.memory_service = MemoryService()
        
        # Start server
        server_thread = threading.Thread(
            target=start_advanced_fridge_server,
            args=(st.session_state.fridge_service, st.session_state.recipe_service),
            daemon=True
        )
        server_thread.start()
        time.sleep(3)
        
        # Connect to server
        def create_transport():
            return streamablehttp_client(f"http://{settings.server_host}:{settings.server_port}/mcp/")
        
        mcp_client = MCPClient(create_transport)
        mcp_client.__enter__()
        
        # Initialize agent
        st.session_state.agent = RecipeAgent(mcp_client, st.session_state.memory_service)
        st.session_state.initialized = True
        st.session_state.messages = []
        st.session_state.profile_setup = False
        st.session_state.fridge_items = []


def setup_user_profile():
    """Setup user profile form."""
    st.title("🍳 Some Good Food - Setup Your Profile")
    st.markdown("Please tell us about your preferences to personalize your experience:")
    
    with st.form("user_profile"):
        dietary = st.text_input("Dietary restrictions (vegetarian, vegan, keto, etc.)")
        dislikes = st.text_input("Foods you avoid (comma separated)")
        cuisines = st.text_input("Favorite cuisines (Italian, Asian, Mexican, etc.)")
        skill = st.selectbox("Cooking skill level", ["beginner", "intermediate", "advanced"])
        
        if st.form_submit_button("Save Profile"):
            # Setup profile with agent
            st.session_state.agent.setup_user_profile(dietary, dislikes, cuisines, skill)
            st.session_state.profile_setup = True
            st.success("Profile saved! You can now start using Some Good Food.")
            st.rerun()


def main():
    st.set_page_config(page_title="🍳 Some Good Food", page_icon="🍳", layout="wide")
    
    # Initialize services
    init_services()
    
    # Initialize session state
    if 'profile_setup' not in st.session_state:
        st.session_state.profile_setup = False
    
    # Check if profile is set up
    if not st.session_state.profile_setup:
        setup_user_profile()
        return
    
    # Header
    st.title("🍳 Some Good Food - Your Smart Kitchen Assistant")
    st.markdown("*Reduce food waste with AI-powered recipe suggestions*")
    
    # Sidebar for fridge management
    with st.sidebar:
        st.header("🧊 Fridge Management")
        
        # Add items
        with st.expander("Add Items"):
            item_name = st.text_input("Item name")
            expiry_date = st.date_input("Expiry date")
            quantity = st.number_input("Quantity", min_value=1, value=1)
            
            if st.button("Add to Fridge"):
                if item_name:
                    response = st.session_state.agent.process_user_input(
                        f"Add {quantity} {item_name} expiring on {expiry_date}"
                    )
                    st.success(f"Added {item_name}")
                    # st.rerun()
            
        # View fridge
        if st.button("View Fridge Contents"):
            response = st.session_state.agent.process_user_input("Show me what's in my fridge")
            st.text_area("Fridge Contents", response, height=200)
    

        
        # Edit preferences
        st.header("⚙️ Preferences")
        with st.expander("Edit Preferences"):
            dietary = st.text_input("Dietary restrictions", key="edit_dietary")
            dislikes = st.text_input("Foods you avoid", key="edit_dislikes")
            cuisines = st.text_input("Favorite cuisines", key="edit_cuisines")
            skill = st.selectbox("Cooking skill", ["beginner", "intermediate", "advanced"], key="edit_skill")
            
            if st.button("Update Preferences"):
                st.session_state.agent.setup_user_profile(dietary, dislikes, cuisines, skill)
                st.success("Preferences updated!")
    
    # Main chat interface
    st.header("💬 Chat with RecipeBot")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask for recipes, add ingredients, or get cooking tips..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.process_user_input(prompt)
            st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        # st.rerun()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 What's Expiring Soon?"):
            response = st.session_state.agent.process_user_input("What items are expiring soon?")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🍽️ Suggest a Recipe"):
            response = st.session_state.agent.process_user_input("Suggest a recipe with my available ingredients")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("📅 Plan This Week"):
            response = st.session_state.agent.process_user_input("Help me plan meals for this week")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


if __name__ == "__main__":
    main()