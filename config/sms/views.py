import os
from openai import OpenAI

def run_sms_voluntary_report_analysis(custom_prompt=None):
    """
    A function to run the SMS voluntary report analysis.
    
    Args:
        custom_prompt (str, optional): Custom prompt for voluntary report analysis
    """
    # Retrieve the API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not found in environment variables."

    try:
        # Initialize the OpenAI client with the retrieved key
        client = OpenAI(api_key=api_key)

        # Make a request to the responses endpoint
        response = client.responses.create(
            model="gpt-5-nano",
            reasoning = {"effort": "medium"},
            text = {"verbosity": "medium"},
            instructions = (
                "Eres un experto en SMS (Safety Management System) y estás encargado de "
                "analizar reportes de seguridad operacional para una escuela de aviación. "
                "Debes ejercer tu función de analista siguiendo los lineamientos del "
                "Anexo 19 de la OACI y las mejores prácticas de la industria aeronáutica. "
                "Utiliza un tono formal y profesional. "
                "IMPORTANTE: Responde ÚNICAMENTE con un JSON válido. NO incluyas texto explicativo antes o después del JSON. "
                "El JSON debe tener exactamente esta estructura: "
                '{ '
                    '"is_valid": "SI", '
                    '"severity": "C", '
                    '"probability": "3", '
                    '"value": "C3", '
                    '"risk_analysis": "Análisis detallado de riesgos del reporte", '
                    '"recommendations": "Recomendaciones específicas para mejorar la seguridad operacional" '
                '} '
                "NOTA: Reemplaza los valores de ejemplo con los valores reales para este reporte específico."
            ),
            input=custom_prompt,
        )

        # Extract the content from the response
        content = response.output_text
        return content
        
    except Exception as e:
        return "API key validation failed. Error: {}".format(e)