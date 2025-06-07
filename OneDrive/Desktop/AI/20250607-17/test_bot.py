import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from logger_config import setup_logger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = setup_logger("bot_test")

class BotTester:
    """Класс для тестирования функциональности бота"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Тестирование наличия переменных окружения"""
        logger.info("Testing environment variables...")
        
        results = {
            "telegram_token": bool(self.telegram_token),
            "openai_api_key": bool(self.openai_api_key)
        }
        
        if results["telegram_token"]:
            logger.info("✅ TELEGRAM_TOKEN found")
        else:
            logger.error("❌ TELEGRAM_TOKEN missing")
        
        if results["openai_api_key"]:
            logger.info("✅ OPENAI_API_KEY found")
        else:
            logger.error("❌ OPENAI_API_KEY missing")
        
        return results
    
    async def test_openai_api(self) -> Dict[str, Any]:
        """Тестирование OpenAI API"""
        logger.info("Testing OpenAI API...")
        
        if not self.openai_client:
            logger.error("❌ OpenAI client not initialized")
            return {"success": False, "error": "OpenAI client not initialized"}
        
        try:
            # Тестовый запрос с координатами Москвы
            test_latitude = 55.7558
            test_longitude = 37.6176
            
            prompt = f"""
            Координаты: {test_latitude}, {test_longitude}

            Найди интересное и необычное место не далее, чем в 3 км от этих координат.
            Расскажи один увлекательный исторический факт, легенду или любопытную особенность об этом месте.
            
            Требования к ответу:
            - Ответ должен быть на русском языке
            - Длина 2-4 предложения  
            - Начни с названия места
            - Сделай рассказ интересным и познавательным
            
            Пример формата ответа:
            "🏛️ Московский Кремль: Знаете ли вы, что..."
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по истории и географии, который рассказывает интересные факты о местах."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            fact = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI API test successful")
            logger.info(f"Generated fact: {fact[:100]}...")
            
            return {
                "success": True,
                "fact": fact,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI API test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_imports(self) -> Dict[str, Any]:
        """Тестирование импортов"""
        logger.info("Testing imports...")
        
        results = {}
        
        try:
            import telegram
            results["telegram"] = True
            logger.info("✅ python-telegram-bot imported successfully")
        except ImportError as e:
            results["telegram"] = False
            logger.error(f"❌ Failed to import telegram: {e}")
        
        try:
            import openai
            results["openai"] = True
            logger.info("✅ openai imported successfully")
        except ImportError as e:
            results["openai"] = False
            logger.error(f"❌ Failed to import openai: {e}")
        
        try:
            from dotenv import load_dotenv
            results["dotenv"] = True
            logger.info("✅ python-dotenv imported successfully")
        except ImportError as e:
            results["dotenv"] = False
            logger.error(f"❌ Failed to import dotenv: {e}")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов"""
        logger.info("Starting comprehensive bot testing...")
        
        results = {
            "imports": self.test_imports(),
            "environment": self.test_environment_variables(),
            "openai_api": await self.test_openai_api()
        }
        
        # Подсчет общих результатов
        total_tests = 0
        passed_tests = 0
        
        # Подсчет импортов
        for test_name, result in results["imports"].items():
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Подсчет переменных окружения
        for test_name, result in results["environment"].items():
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Подсчет API тестов
        total_tests += 1
        if results["openai_api"]["success"]:
            passed_tests += 1
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests) * 100
        }
        
        logger.info(f"Testing completed: {passed_tests}/{total_tests} tests passed ({results['summary']['success_rate']:.1f}%)")
        
        return results

async def main():
    """Основная функция тестирования"""
    tester = BotTester()
    results = await tester.run_all_tests()
    
    print("\n" + "="*50)
    print("BOT TESTING RESULTS")
    print("="*50)
    
    print(f"\nIMPORTS:")
    for lib, status in results["imports"].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {lib}")
    
    print(f"\nENVIRONMENT VARIABLES:")
    for var, status in results["environment"].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {var}")
    
    print(f"\nAPI TESTS:")
    openai_status = "✅" if results["openai_api"]["success"] else "❌"
    print(f"  {openai_status} OpenAI API")
    
    if results["openai_api"]["success"]:
        print(f"    Generated fact: {results['openai_api']['fact'][:100]}...")
        print(f"    Tokens used: {results['openai_api'].get('tokens_used', 'N/A')}")
    else:
        print(f"    Error: {results['openai_api'].get('error', 'Unknown error')}")
    
    print(f"\nSUMMARY:")
    summary = results["summary"]
    print(f"  Tests passed: {summary['passed_tests']}/{summary['total_tests']}")
    print(f"  Success rate: {summary['success_rate']:.1f}%")
    
    if summary['success_rate'] == 100:
        print("\n🎉 All tests passed! Bot is ready for deployment.")
    else:
        print(f"\n⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    asyncio.run(main()) 