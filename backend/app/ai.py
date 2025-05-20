import os
import json
from typing import List, Dict, Any, Tuple
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('root_cause_ai')

class RootCauseAI:
    """
    AI module for suggesting root causes based on historical data
    using Gemini model through Langchain
    """
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.model = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash-preview-04-17",
            google_api_key=self.gemini_api_key,
            temperature=0.2
        )
        
        # ===== Cara mengganti model ke DeepSeek AI =====
        # 1. Install langchain-deepseek:
        # pip install -U langchain-deepseek
        #
        # 2. Import DeepSeek integration:
        # from langchain_deepseek import ChatDeepSeek
        #
        # 3. Tambahkan deepseek_api_key ke .env file:
        # DEEPSEEK_API_KEY=your_api_key_here
        #
        # 4. Ganti kode di atas dengan ini:
        # self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        # self.model = ChatDeepSeek(
        #     model="deepseek-chat",  # atau model lain sesuai kebutuhan
        #     temperature=0.2
        # )
        #
        # ===== Cara mengganti model ke OpenAI (GPT) =====
        # 1. Install langchain-openai:
        # pip install -U langchain-openai
        #
        # 2. Import OpenAI integration:
        # from langchain_openai import ChatOpenAI
        #
        # 3. Tambahkan openai_api_key ke .env file:
        # OPENAI_API_KEY=your_api_key_here
        #
        # 4. Ganti kode di atas dengan ini:
        # self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # self.model = ChatOpenAI(
        #     model="gpt-4-turbo",  # atau model lain seperti gpt-3.5-turbo
        #     openai_api_key=self.openai_api_key,
        #     temperature=0.2
        # )
        
    def create_root_cause_prompt(self, area: str, problem: str, category: str, historical_data: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for the AI model to suggest root causes
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            category (str): Category of the problem (4M+1E)
            historical_data (list): List of historical data (optimized) from database
            
        Returns:
            PromptTemplate: Configured prompt template for the AI
        """
        # Convert historical data to a formatted string for the prompt
        historical_examples = ""

        if historical_data:
            valid_records = [r for r in historical_data if isinstance(r, dict) and all(k in r for k in ['area', 'problem', 'root_cause', 'category'])]
            if not valid_records:
                historical_examples = "No valid historical data available (missing keys).\n"
            else:
                for i, record in enumerate(valid_records[:10]):  # Limit to 10 examples to avoid token limits
                    historical_examples += f"Example {i+1}:\n"
                    historical_examples += f"- Area: {record['area']}\n"
                    historical_examples += f"- Problem: {record['problem']}\n"
                    historical_examples += f"- Root Cause: {record['root_cause']}\n"
                    historical_examples += f"- Category: {record['category']}\n\n"
        else:
            historical_examples = "No historical data available for this area.\n"
        
        template = f"""
        Anda adalah AI expert untuk analisa root cause di industri manufaktur packaging.
        
        ## Instruksi:
        - Berikan jawaban dalam **Bahasa Indonesia** yang natural, seperti catatan teknisi di database.
        - Gunakan istilah teknis dalam bahasa Inggris **hanya untuk istilah mesin/teknis**,
          namun penjelasan dan kalimat utama tetap dominan Bahasa Indonesia.
        - Gaya bahasa harus mirip data historis di database: campuran, tidak full English.
        - Jawaban harus singkat, padat, dan mudah dipahami operator/teknisi.
        - Perbaiki semua jawaban agar jelas dan terstruktur, bahkan jika data historis menggunakan kata-kata yang kurang jelas.
        - Berikan jawaban yang tegas dan spesifik tanpa keraguan
        - Hindari penggunaan tanda "/" dalam jawaban
        - Pilih satu istilah yang paling tepat, jangan memberikan alternatif
        
        ## Context:
        - Area: {{area}}
        - Category (4M+1E): {{category}}
        - Problem: {{problem}}
        
        ## Data Historis (area & category sama):
        {{historical_data}}
        
        ## Task:
        Berdasarkan problem dan pola historis, berikan 3-5 root cause paling mungkin.
        
        Format jawaban: JSON array string, contoh:
        ["Root cause 1", "Root cause 2", "Root cause 3"]
        
        ## Penting:
        - Jika problem sangat mirip dengan data historis, prioritaskan root cause tersebut.
        - Jika tidak ada data mirip, gunakan pengetahuan manufaktur umum.
        - Jawaban harus relevan dengan area, problem, dan category.
        - **Jangan gunakan full English** kecuali istilah teknis.
        """
        
        prompt = PromptTemplate(
            input_variables=["area", "problem", "category", "historical_data"],
            template=template
        )
        
        return prompt
    
    def suggest_root_causes(self, area: str, problem: str, category: str, historical_data: List[Dict[str, Any]]) -> List[str]:
        """
        Generate root cause suggestions using LLM reasoning
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            category (str): Category (4M+1E) of the problem
            historical_data (list): List of semantically filtered historical data from database
            containing only area, problem, root_cause, and category columns
            
        Returns:
            list: List of suggested root causes
        """
        try:
            # Create prompt with the semantically filtered data from database
            prompt = self.create_root_cause_prompt(area, problem, category, historical_data)
            
            # Use the modern pattern with | operator instead of deprecated LLMChain
            chain = prompt | self.model
            
            # Create a structured historical data string focusing only on problem and root cause
            valid_records = [r for r in historical_data if isinstance(r, dict) and all(k in r for k in ['area', 'problem', 'root_cause', 'category'])]
            if not valid_records:
                historical_data_str = "No valid historical data available (missing keys)."
            else:
                # Limit to only top 5 records to minimize token usage
                top_records = valid_records[:5]
                historical_data_str = "\n".join([f"- Area: {record['area']}\n  Problem: {record['problem']}\n  Root Cause: {record['root_cause']}\n  Category: {record['category']}" for record in top_records])
                if len(valid_records) > 5:
                    historical_data_str += f"\n(Showing top 5 of {len(valid_records)} records)"
            
            # Prepare input for logging
            input_data = {
                "area": area,
                "problem": problem,
                "category": category,
                "historical_data": historical_data_str
            }
            
            # Log the prompt being sent to the AI
            logger.info(f"\n{'='*50}\nAPI CALL: suggest_root_causes\n{'='*50}")
            logger.info(f"PROMPT:\n{prompt.template}")
            logger.info(f"INPUT DATA:\n{json.dumps(input_data, indent=2, ensure_ascii=False)}")
            
            # Invoke the AI model
            result = chain.invoke(input_data)
            
            # Log the raw response from the AI
            raw_response = result.content if hasattr(result, 'content') else str(result)
            logger.info(f"RAW AI RESPONSE:\n{raw_response}\n{'='*50}")
            # Modern LangChain returns AIMessage objects
            # Extract the text content from the AIMessage
            if hasattr(result, 'content'):
                result = result.content
            elif isinstance(result, dict) and "text" in result:
                result = result["text"]
            
            # Process the result to extract the list of root causes
            # Expecting a JSON array from the LLM
            # json is already imported at the top of the file
            try:
                # Clean up the result to make sure it's a valid JSON array
                cleaned_result = result.strip() if isinstance(result, str) else str(result).strip()
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
                
                suggested_causes = json.loads(cleaned_result)
                return suggested_causes
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                # Split by newlines or commas if the LLM didn't return proper JSON
                fallback_causes = [
                    cause.strip() 
                    for cause in result.replace("[", "").replace("]", "").replace('"', "").split(",")
                    if cause.strip()
                ]
                return fallback_causes[:5]  # Limit to 5 causes
                
        except Exception as e:
            print(f"Error in AI suggestion: {str(e)}")
            return ["Error generating suggestions. Please try again."]
            
    def analyze_and_merge_root_causes(self, root_causes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of root causes from different users and merge similar ones
        while preserving all user information
        
        Args:
            root_causes_data (list): List of dictionaries with 'root_cause' and 'user_id' keys
            
        Returns:
            dict: A dictionary containing both merged and original root causes with user information
        """
        try:
            # Create the prompt for analyzing and merging similar root causes
            template = """
            Anda adalah AI expert untuk analisa root cause di industri manufaktur packaging.
            
            ## Instruksi:
            - Analisis daftar root cause berikut yang berasal dari berbagai user
            - Identifikasi root cause yang mirip atau memiliki maksud yang sama
            - Gabungkan (merge) root cause yang mirip tersebut menjadi satu formulasi yang lebih baik
            - Tetap pertahankan informasi user_id untuk setiap root cause, bahkan yang sudah digabungkan
            - Berikan jawaban dalam format JSON yang mudah diproses
            
            ## Data Root Cause dari Berbagai User:
            {root_causes_json}
            
            ## Format Output yang Diharapkan:
            ```json
            {{
              "merged_root_causes": [
                {{
                  "merged_root_cause": "[Root cause hasil penggabungan]",
                  "original_data": [
                    {{ "root_cause": "[original root cause 1]", "user_id": "[user_id 1]" }},
                    {{ "root_cause": "[original root cause 2]", "user_id": "[user_id 2]" }}
                  ]
                }}
              ],
              "individual_root_causes": [
                {{ "root_cause": "[root cause yang tidak digabung]", "user_id": "[user_id]" }}
              ]
            }}
            ```
            
            ## Penting:
            - Root cause yang sangat mirip harus digabung menjadi satu formulasi yang lebih baik
            - Root cause yang berbeda harus dipertahankan sebagai individual
            - Setiap root cause (baik yang digabung maupun individual) harus mempertahankan informasi user_id aslinya
            - JSON output harus valid dan mengikuti format yang ditentukan
            
            Berikan output JSON-nya saja, tanpa penjelasan tambahan:
            """
            
            # Convert the root causes data to JSON string for the prompt
            root_causes_json = json.dumps(root_causes_data, ensure_ascii=False, indent=2)
            
            # Create a prompt template
            prompt = PromptTemplate(input_variables=["root_causes_json"], template=template)
            
            # Use the modern pattern with | operator
            chain = prompt | self.model
            
            # Log the prompt being sent to the AI
            logger.info(f"\n{'='*50}\nAPI CALL: analyze_and_merge_root_causes\n{'='*50}")
            logger.info(f"PROMPT:\n{prompt.template}")
            logger.info(f"INPUT DATA:\n{root_causes_json}")
            
            # Invoke the chain with the JSON string
            result = chain.invoke({"root_causes_json": root_causes_json})
            
            # Log the raw response from the AI
            raw_response = result.content if hasattr(result, 'content') else str(result)
            logger.info(f"RAW AI RESPONSE:\n{raw_response}\n{'='*50}")
            
            # Extract the text content from the AIMessage
            if hasattr(result, 'content'):
                result = result.content
            elif isinstance(result, dict) and "text" in result:
                result = result["text"]
            
            # Process the result to extract the JSON output
            try:
                # Clean up the result to make sure it's a valid JSON
                cleaned_result = result.strip() if isinstance(result, str) else str(result).strip()
                
                # Remove code block markers if present
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
                elif cleaned_result.startswith("```"):
                    cleaned_result = cleaned_result.replace("```", "", 2).strip()
                
                # Parse the JSON result
                merged_result = json.loads(cleaned_result)
                
                # Add a field to track all original data for reference
                merged_result["all_original_data"] = root_causes_data
                
                return merged_result
                
            except json.JSONDecodeError as e:
                # Return an error message if JSON parsing fails
                print(f"Error parsing AI response as JSON: {str(e)}")
                return {
                    "error": "Failed to parse AI response",
                    "merged_root_causes": [],
                    "individual_root_causes": root_causes_data,
                    "all_original_data": root_causes_data
                }
                
        except Exception as e:
            print(f"Error in AI merging analysis: {str(e)}")
            return {
                "error": f"Error analyzing root causes: {str(e)}",
                "merged_root_causes": [],
                "individual_root_causes": root_causes_data,
                "all_original_data": root_causes_data
            }

    def create_action_prompt(self, area: str, problem: str, root_cause: str, category: str, historical_data: List[Dict[str, Any]]) -> PromptTemplate:
        """
        Create a prompt for the AI model to suggest temporary and preventive actions
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            root_cause (str): Identified root cause of the problem
            category (str): Category of the problem (4M+1E)
            historical_data (list): List of historical data (optimized) from database
            
        Returns:
            PromptTemplate: Configured prompt template for the AI
        """
        # Convert historical data to a formatted string for the prompt
        historical_examples = ""

        if historical_data:
            valid_records = [r for r in historical_data if isinstance(r, dict) and 
                           all(k in r for k in ['area', 'problem', 'root_cause', 'category', 'temporary_action', 'preventive_action'])]
            if not valid_records:
                historical_examples = "No valid historical data available (missing action fields).\n"
            else:
                for i, record in enumerate(valid_records[:10]):  # Limit to 10 examples to avoid token limits
                    historical_examples += f"Example {i+1}:\n"
                    historical_examples += f"- Area: {record['area']}\n"
                    historical_examples += f"- Problem: {record['problem']}\n"
                    historical_examples += f"- Root Cause: {record['root_cause']}\n"
                    historical_examples += f"- Category: {record['category']}\n"
                    historical_examples += f"- Temporary Action: {record['temporary_action']}\n"
                    historical_examples += f"- Preventive Action: {record['preventive_action']}\n\n"
        else:
            historical_examples = "No historical data available for this area and category.\n"
        
        template = """
        Anda adalah AI expert untuk menganalisa dan membuat temporary action dan preventive action di industri manufaktur packaging.
        
        ## Instruksi:
        - Berikan jawaban dalam **Bahasa Indonesia** yang natural, seperti catatan teknisi di database.
        - Gunakan istilah teknis dalam bahasa Inggris **hanya untuk istilah mesin/teknis**,
          namun penjelasan dan kalimat utama tetap dominan Bahasa Indonesia.
        - Gaya bahasa harus mirip data historis di database: campuran, tidak full English.
        - Jawaban harus singkat, padat, dan mudah dipahami operator/teknisi.
        - Perbaiki semua jawaban agar jelas dan terstruktur, bahkan jika data historis menggunakan kata-kata yang kurang jelas.
        - Berikan jawaban yang tegas dan spesifik tanpa keraguan
        - Hindari penggunaan tanda "/" dalam jawaban
        - Pilih satu istilah yang paling tepat, jangan memberikan alternatif
        
        ## Context:
        - Area: {area}
        - Category (4M+1E): {category}
        - Problem: {problem}
        - Root Cause: {root_cause}
        
        ## Data Historis (area & category sama):
        {historical_data}
        
        ## Task:
        Berdasarkan problem, root cause, dan pola historis, berikan saran untuk:
        1. Temporary Action (3-5 saran) - tindakan cepat untuk mengatasi masalah sementara
        2. Preventive Action (3-5 saran) - tindakan pencegahan jangka panjang agar masalah tidak terulang
        
        Format jawaban: JSON dengan format:
        ```json
        {{{{
            "temporary_actions": ["Temporary action 1", "Temporary action 2", "Temporary action 3"],
            "preventive_actions": ["Preventive action 1", "Preventive action 2", "Preventive action 3"]
        }}}}
        ```
        
        ## Penting:
        - Jika problem sangat mirip dengan data historis, prioritaskan tindakan yang pernah berhasil.
        - Jika tidak ada data mirip, gunakan pengetahuan manufaktur umum.
        - Jawaban harus relevan dengan area, problem, root cause, dan category.
        - **Jangan gunakan full English** kecuali istilah teknis.
        - Temporary action fokus pada solusi cepat untuk mengatasi gejala.
        - Preventive action fokus pada solusi jangka panjang yang mengatasi akar masalah.
        """
        
        prompt = PromptTemplate(
            input_variables=["area", "problem", "root_cause", "category", "historical_data"],
            template=template
        )
        
        return prompt
    
    def create_scoring_prompt(self, area: str, problem: str, category: str, root_causes: List[str]) -> PromptTemplate:
        """
        Create a prompt for the AI model to score root causes based on quality benchmark criteria
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            category (str): Category of the problem (4M+1E)
            root_causes (list): List of root causes to be scored
            
        Returns:
            PromptTemplate: Configured prompt template for the AI
        """
        # Format the root causes as a numbered list for the prompt
        root_causes_text = ""
        for i, cause in enumerate(root_causes):
            root_causes_text += f"{i+1}. {cause}\n"
        
        template = """
        Anda adalah AI expert untuk analisa root cause di industri manufaktur packaging.
        
        ## Instruksi:
        - Berikan penilaian (scoring) untuk setiap root cause yang diinput user
        - Gunakan kriteria benchmark sebagai acuan penilaian
        - Setiap root cause diberi nilai berdasarkan kualitas, relevansi, dan kejelasannya
        - Berikan jawaban dalam format JSON yang mudah diproses
        
        ## Context:
        - Area: {area}
        - Category (4M+1E): {category}
        - Problem: {problem}
        
        ## Root Causes untuk Dinilai:
        {root_causes_text}
        
        ## Kriteria Benchmark Penilaian:
        1. Spesifisitas (0-2.5 poin): Seberapa spesifik root cause dalam menjelaskan masalah
            - 0-0.5: Sangat umum, tidak spesifik
            - 0.6-1.5: Cukup spesifik
            - 1.6-2.5: Sangat spesifik dan detail
            
        2. Relevansi dengan Problem (0-2.5 poin): Seberapa relevan root cause dengan problem yang dijelaskan
            - 0-0.5: Tidak relevan dengan problem
            - 0.6-1.5: Cukup relevan
            - 1.6-2.5: Sangat relevan dan tepat sasaran
            
        3. Kejelasan Analisis (0-2.5 poin): Seberapa jelas root cause dalam mengidentifikasi penyebab
            - 0-0.5: Tidak jelas, membingungkan
            - 0.6-1.5: Cukup jelas
            - 1.6-2.5: Sangat jelas dan mudah dipahami
            
        4. Actionability (0-2.5 poin): Seberapa mudah root cause dapat ditindaklanjuti
            - 0-0.5: Sulit untuk ditindaklanjuti
            - 0.6-1.5: Cukup dapat ditindaklanjuti
            - 1.6-2.5: Sangat mudah untuk ditindaklanjuti
        
        ## Format Jawaban:
        Berikan output JSON dengan format:
        ```json
        {{
          "scores": [
            {{
              "root_cause": "Root cause 1",
              "spesifisitas": 2.0,
              "relevansi": 1.8,
              "kejelasan": 2.2,
              "actionability": 1.9,
              "total_score": 7.9,
              "feedback": "Feedback singkat tentang root cause ini"
            }},
            {{
              "root_cause": "Root cause 2",
              "spesifisitas": 1.5,
              "relevansi": 2.0,
              "kejelasan": 1.8,
              "actionability": 1.6,
              "total_score": 6.9,
              "feedback": "Feedback singkat tentang root cause ini"
            }}
          ],
          "summary": "Rangkuman singkat tentang hasil penilaian keseluruhan"
        }}
        ```
        
        ## Penting:
        - Berikan nilai yang objektif sesuai dengan kriteria benchmark
        - Total score adalah jumlah dari semua kriteria (max 10 poin)
        - Feedback harus singkat, konstruktif, dan dalam Bahasa Indonesia
        - Summary harus memberikan gambaran keseluruhan hasil penilaian
        
        Berikan output JSON-nya saja, tanpa penjelasan tambahan:
        """
        
        prompt = PromptTemplate(
            input_variables=["area", "problem", "category", "root_causes_text"],
            template=template
        )
        
        return prompt
    
    def score_root_causes(self, area: str, problem: str, category: str, root_causes: List[str]) -> Dict[str, Any]:
        """
        Score root causes based on quality benchmark criteria
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            category (str): Category (4M+1E) of the problem
            root_causes (list): List of root causes to be scored
            
        Returns:
            dict: Dictionary with scores and feedback for each root cause
        """
        try:
            # Create the prompt for scoring root causes
            prompt = self.create_scoring_prompt(area, problem, category, root_causes)
            
            # Use the modern pattern with | operator
            chain = prompt | self.model
            
            # Format root causes as text for the prompt
            root_causes_text = ""
            for i, cause in enumerate(root_causes):
                root_causes_text += f"{i+1}. {cause}\n"
            
            # Prepare input for logging
            input_data = {
                "area": area,
                "problem": problem,
                "category": category,
                "root_causes_text": root_causes_text
            }
            
            # Log the prompt being sent to the AI
            logger.info(f"\n{'='*50}\nAPI CALL: score_root_causes\n{'='*50}")
            logger.info(f"PROMPT:\n{prompt.template}")
            logger.info(f"INPUT DATA:\n{json.dumps(input_data, indent=2, ensure_ascii=False)}")
            
            # Invoke the chain with the input variables
            result = chain.invoke(input_data)
            
            # Log the raw response from the AI
            raw_response = result.content if hasattr(result, 'content') else str(result)
            logger.info(f"RAW AI RESPONSE:\n{raw_response}\n{'='*50}")
            
            # Extract the text content from the AIMessage
            if hasattr(result, 'content'):
                result = result.content
            elif isinstance(result, dict) and "text" in result:
                result = result["text"]
            
            # Process the result to extract the JSON output
            # json is already imported at the top of the file
            try:
                # Clean up the result to make sure it's a valid JSON
                cleaned_result = result.strip() if isinstance(result, str) else str(result).strip()
                
                # Remove code block markers if present
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
                elif cleaned_result.startswith("```"):
                    cleaned_result = cleaned_result.replace("```", "", 2).strip()
                
                # Parse the JSON result
                scoring_result = json.loads(cleaned_result)
                
                # Ensure the expected keys are present
                if "scores" not in scoring_result:
                    raise ValueError("Missing 'scores' key in AI response")
                
                return scoring_result
                
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if JSON parsing fails
                print(f"Error parsing AI scoring response: {str(e)}")
                # Return a basic error response
                return {
                    "error": f"Error parsing scoring result: {str(e)}",
                    "scores": [{
                        "root_cause": cause,
                        "total_score": 0,
                        "feedback": "Error saat menilai root cause."
                    } for cause in root_causes],
                    "summary": "Terjadi kesalahan dalam proses penilaian. Silakan coba lagi."
                }
                
        except Exception as e:
            print(f"Error in AI root cause scoring: {str(e)}")
            return {
                "error": f"Error scoring root causes: {str(e)}",
                "scores": [{
                    "root_cause": cause,
                    "total_score": 0,
                    "feedback": "Error saat menilai root cause."
                } for cause in root_causes],
                "summary": "Terjadi kesalahan dalam proses penilaian. Silakan coba lagi."
            }
    
    def suggest_actions(self, area: str, problem: str, root_cause: str, category: str, historical_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Generate temporary and preventive action suggestions using LLM reasoning
        
        Args:
            area (str): Area where the problem occurred
            problem (str): Description of the problem
            root_cause (str): Identified root cause of the problem
            category (str): Category (4M+1E) of the problem
            historical_data (list): List of semantically filtered historical data from database
            
        Returns:
            dict: Dictionary with lists of suggested temporary and preventive actions
        """
        try:
            # Create the prompt for action suggestions with semantically filtered data from database
            prompt = self.create_action_prompt(area, problem, root_cause, category, historical_data)
            
            # Use the modern pattern with | operator
            chain = prompt | self.model
            
            # Create a structured historical data string focusing on actions
            valid_records = [r for r in historical_data if isinstance(r, dict) and 
                           all(k in r for k in ['area', 'problem', 'root_cause', 'category', 'temporary_action', 'preventive_action'])]
            if not valid_records:
                historical_data_str = "No valid historical data available (missing action fields)."
            else:
                # Limit to only top 5 records to minimize token usage
                top_records = valid_records[:5]
                historical_data_str = "\n".join([
                    f"- Area: {record['area']}\n  Problem: {record['problem']}\n  Root Cause: {record['root_cause']}\n  "
                    f"Category: {record['category']}\n  Temporary Action: {record['temporary_action']}\n  "
                    f"Preventive Action: {record['preventive_action']}" 
                    for record in top_records
                ])
                if len(valid_records) > 5:
                    historical_data_str += f"\n(Showing top 5 of {len(valid_records)} records)"
            
            # Prepare input for logging
            input_data = {
                "area": area,
                "problem": problem,
                "root_cause": root_cause,
                "category": category,
                "historical_data": historical_data_str
            }
            
            # Log the prompt being sent to the AI
            logger.info(f"\n{'='*50}\nAPI CALL: suggest_actions\n{'='*50}")
            logger.info(f"PROMPT:\n{prompt.template}")
            logger.info(f"INPUT DATA:\n{json.dumps(input_data, indent=2, ensure_ascii=False)}")
            
    
            # Invoke the chain with the input variables
            result = chain.invoke(input_data)
            
            # Log the raw response from the AI
            raw_response = result.content if hasattr(result, 'content') else str(result)
            logger.info(f"RAW AI RESPONSE:\n{raw_response}\n{'='*50}")
            
            # Extract the text content from the AIMessage
            if hasattr(result, 'content'):
                result = result.content
            elif isinstance(result, dict) and "text" in result:
                result = result["text"]
            
            # Process the result to extract the JSON output
            # json is already imported at the top of the file
            try:
                # Clean up the result to make sure it's a valid JSON
                cleaned_result = result.strip() if isinstance(result, str) else str(result).strip()
                
                # Remove code block markers if present
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
                elif cleaned_result.startswith("```"):
                    cleaned_result = cleaned_result.replace("```", "", 2).strip()
                
                # Parse the JSON result
                actions = json.loads(cleaned_result)
                
                # Ensure the expected keys are present
                if "temporary_actions" not in actions or "preventive_actions" not in actions:
                    raise ValueError("Missing expected keys in AI response")
                
                return actions
                
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback if JSON parsing fails
                print(f"Error parsing AI response: {str(e)}")
                # Attempt basic extraction if possible
                temp_actions = []
                prev_actions = []
                
                # Very basic fallback parsing
                if "temporary" in result.lower():
                    temp_section = result.lower().split("temporary")[1].split("preventive")[0]
                    temp_actions = [line.strip() for line in temp_section.split("\n") if line.strip() and "-" in line]
                
                if "preventive" in result.lower():
                    prev_section = result.lower().split("preventive")[1]
                    prev_actions = [line.strip() for line in prev_section.split("\n") if line.strip() and "-" in line]
                
                return {
                    "temporary_actions": temp_actions[:5] if temp_actions else ["Error parsing temporary actions"],
                    "preventive_actions": prev_actions[:5] if prev_actions else ["Error parsing preventive actions"]
                }
                
        except Exception as e:
            print(f"Error in AI action suggestion: {str(e)}")
            return {
                "temporary_actions": ["Error generating temporary action suggestions. Please try again."],
                "preventive_actions": ["Error generating preventive action suggestions. Please try again."]
            }
