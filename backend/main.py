from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sympy import symbols, solve, sympify
from scipy.optimize import minimize
import numpy as np
from typing import Dict, Any
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mathematical Computation API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class EquationInput(BaseModel):
    equation: str  # LaTeX format equation

class FunctionInput(BaseModel):
    function: str  # LaTeX format function
    domain: tuple[float, float] = (-10, 10)  # Default domain for analysis

class ComputationResult(BaseModel):
    status: str
    result: Dict[str, Any]
    latex_format: str  # LaTeX formatted result

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {"message": "Mathematical Computation API is running"}

@app.post("/solve-equation", response_model=ComputationResult)
async def solve_equation(input_data: EquationInput):
    """
    Solves a mathematical equation using SymPy.
    Expects LaTeX format equation like 'x^2 + 5x + 6 = 0'
    """
    try:
        # Convert LaTeX to SymPy format
        eq_str = input_data.equation.replace('^', '**')
        
        # Handle multiplication with x (convert 5x to 5*x)
        eq_str = ''.join(
            f"*{c}" if i > 0 and c == 'x' and eq_str[i-1].isdigit() 
            else c 
            for i, c in enumerate(eq_str)
        )
        
        # Remove '= 0' if present and move everything to LHS
        if '=' in eq_str:
            left, right = eq_str.split('=')
            eq_str = f"({left.strip()})-({right.strip()})"
        
        x = symbols('x')
        equation = sympify(eq_str)
        solutions = solve(equation, x)
        
        # Convert solutions to LaTeX format
        latex_solutions = [f'x_{{{i+1}}} = {sol}' for i, sol in enumerate(solutions)]
        
        return ComputationResult(
            status="success",
            result={
                "solutions": [str(sol) for sol in solutions],
                "original_equation": input_data.equation
            },
            latex_format=' \\quad '.join(latex_solutions)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/optimize-function", response_model=ComputationResult)
async def optimize_function(input_data: FunctionInput):
    """
    Finds minimum and maximum values of a function using SciPy.
    Expects LaTeX format function like 'x^3 + 3x^2 + 9'
    """
    try:
        # Convert LaTeX to Python format
        func_str = input_data.function.replace('^', '**')
        
        # Handle implicit multiplication with x (convert 3x to 3*x)
        func_str = ''.join(
            f"*{c}" if i > 0 and c == 'x' and func_str[i-1].isdigit() 
            else c 
            for i, c in enumerate(func_str)
        )
        
        # Create lambda function for optimization
        # Add logging to see the function string
        print(f"Processing function: {func_str}")
        func = lambda x: eval(func_str, {"x": x, "np": np})
        
        # Find minimum
        min_result = minimize(func, x0=0, bounds=[input_data.domain])
        
        # Find maximum by minimizing negative of function
        max_result = minimize(lambda x: -func(x), x0=0, bounds=[input_data.domain])
        
        results = {
            "minimum": {
                "point": float(min_result.x[0]),
                "value": float(min_result.fun)
            },
            "maximum": {
                "point": float(max_result.x[0]),
                "value": float(-max_result.fun)
            },
            "original_function": input_data.function
        }
        
        # Create LaTeX format result
        latex_result = f"""\\begin{{cases}}
        \\text{{Minimum:}} & f({results['minimum']['point']:.2f}) = {results['minimum']['value']:.2f} \\\\
        \\text{{Maximum:}} & f({results['maximum']['point']:.2f}) = {results['maximum']['value']:.2f}
        \\end{{cases}}"""
        
        return ComputationResult(
            status="success",
            result=results,
            latex_format=latex_result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)