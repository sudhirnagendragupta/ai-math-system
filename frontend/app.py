import streamlit as st
from openai import OpenAI
import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Backend API URL
API_BASE_URL = "http://localhost:8000"

class MathematicalAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def extract_math_expression(self, text: str) -> dict:
        """
        Uses GPT-4 to extract mathematical expressions from natural language
        and determine the computation type.
        """
        prompt = f"""
        Extract the mathematical expression from this text and identify the computation type.
        Text: {text}
        
        Return a JSON object with the following structure:
        {{
            "type": "equation" or "optimization",
            "expression": "the mathematical expression in LaTeX format",
            "original_query": "the original text"
        }}
        
        Important formatting rules:
        1. For equations, convert to the form "... = 0"
        2. For functions to optimize:
           - Keep only the function expression
           - Ensure all multiplication with x is explicit (e.g., "3*x" not "3x")
           - Use proper power notation (e.g., "x^3" or "x**3")
        
        Examples:
        "Solve x^2 + 5x + 6 = 0" ->
        {{
            "type": "equation",
            "expression": "x^2 + 5*x + 6 = 0",
            "original_query": "Solve x^2 + 5x + 6 = 0"
        }}
        
        "Find the minimum of x^3 + 3x^2 + 9" ->
        {{
            "type": "optimization",
            "expression": "x^3 + 3*x^2 + 9",
            "original_query": "Find the minimum of x^3 + 3x^2 + 9"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a mathematical expression parser. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                st.error("Failed to parse GPT response as JSON")
                return None
        except Exception as e:
            st.error(f"Error in expression extraction: {str(e)}")
            return None

    def explain_result(self, query: str, result: dict) -> str:
        """
        Generates a natural language explanation of the mathematical result.
        """
        prompt = f"""
        Explain this mathematical result in clear, educational terms.
        Original query: {query}
        Result: {result}
        
        Provide a step-by-step explanation including:
        1. What was being solved/computed
        2. The method used
        3. The interpretation of the results
        4. Any important mathematical insights or observations
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful math tutor explaining results."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error generating explanation: {str(e)}")
            return "I apologize, but I couldn't generate an explanation at this time."

def main():
    st.set_page_config(
        page_title="AI Mathematical Assistant",
        page_icon="🧮",
        layout="wide"
    )

    st.title("AI Mathematical Assistant")
    st.markdown("""
    Ask me to solve equations or find minimum/maximum values of functions using natural language!
    
    Example queries:
    - "Solve the equation x^2 + 5x + 6 = 0"
    - "Find the minimum and maximum values of x^2 - 4x + 3"
    - "What are the solutions to 2x^2 - 8 = 0?"
    """)

    # Initialize the assistant
    assistant = MathematicalAssistant()

    # Get user input
    user_query = st.text_input("Enter your mathematical query:", 
                              placeholder="e.g., Solve x^2 + 5x + 6 = 0")

    if st.button("Solve") and user_query:
        with st.spinner("Analyzing your query..."):
            # Extract mathematical expression and determine computation type
            parsed = assistant.extract_math_expression(user_query)
            
            if parsed:
                st.markdown("### Parsed Expression")
                st.latex(parsed["expression"])
                
                try:
                    # Call appropriate API endpoint based on computation type
                    if parsed["type"] == "equation":
                        response = requests.post(
                            f"{API_BASE_URL}/solve-equation",
                            json={"equation": parsed["expression"]}
                        )
                    else:  # optimization
                        response = requests.post(
                            f"{API_BASE_URL}/optimize-function",
                            json={"function": parsed["expression"]}
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        st.markdown("### Solution")
                        st.latex(result["latex_format"])
                        
                        # Get and display explanation
                        with st.spinner("Generating explanation..."):
                            explanation = assistant.explain_result(user_query, result)
                            st.markdown("### Explanation")
                            st.markdown(explanation)
                    else:
                        st.error(f"Computation error: {response.text}")
                
                except Exception as e:
                    st.error(f"Error during computation: {str(e)}")
            else:
                st.error("Could not parse the mathematical expression.")

    # Add information about LaTeX support
    with st.expander("ℹ️ Using Mathematical Notation"):
        st.markdown("""
        You can use standard mathematical notation in your queries. The system supports LaTeX-style formatting:
        
        - Powers: Use `^` (e.g., `x^2` for x²)
        - Multiplication: Use `*` or just write variables next to each other (e.g., `2x` or `2*x`)
        - Division: Use `/` (e.g., `x/2`)
        - Functions: Use standard notation (e.g., `sin(x)`, `cos(x)`, `exp(x)`)
        
        Examples:
        - `x^2 + 5x + 6`
        - `2*x^3 - 3*x^2 + 1`
        - `sin(x)^2 + cos(x)^2`
        """)

    # System capabilities
    with st.expander("🔧 System Capabilities"):
        st.markdown("""
        This AI-enhanced mathematical assistant can:
        
        1. **Solve Equations**
           - Polynomial equations
           - Rational equations
           - Transcendental equations
        
        2. **Optimize Functions**
           - Find minimum values
           - Find maximum values
           - Analyze function behavior
        
        3. **Provide Explanations**
           - Step-by-step solutions
           - Mathematical insights
           - Educational context
        """)

if __name__ == "__main__":
    main()