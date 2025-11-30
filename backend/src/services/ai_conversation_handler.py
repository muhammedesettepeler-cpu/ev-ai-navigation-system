"""
AI Conversation Handler - Simplified Version

Primary AI: Google Gemini 2.0 Flash (fast and intelligent)
Fallback AI: OpenRouter (if Gemini fails)

Only chat and vehicle search functionality - no complex conversation state
"""

import logging
import os
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# ==================== AI Providers Setup ====================

GEMINI_AVAILABLE = False
OPENROUTER_AVAILABLE = False

gemini_model = None
openrouter_client = None

# Setup Gemini 2.0 Flash (Primary AI)
try:
    import google.generativeai as genai  # type: ignore

    gemini_api_key = os.getenv(
        "GEMINI_API_KEY", "AIzaSyDazeipPR2QP3f1Gd0ee7HKClMGl9b1pM0"
    )

    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)  # type: ignore
        gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")  # type: ignore
        GEMINI_AVAILABLE = True
        logger.info("Gemini 2.0 Flash initialized (Primary AI)")
    else:
        logger.warning("Gemini API key not found")

except ImportError as e:
    logger.warning(f"Google Generative AI package not available: {e}")
except Exception as e:
    logger.error(f"Gemini initialization failed: {e}")

# Setup OpenRouter (Fallback AI)
try:
    from openai import OpenAI

    openrouter_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=openrouter_key
        )
        OPENROUTER_AVAILABLE = True
        logger.info("OpenRouter initialized (Fallback AI)")
    else:
        logger.warning("OpenRouter API key not found")

except ImportError as e:
    logger.warning(f"OpenAI package not available: {e}")
except Exception as e:
    logger.error(f"OpenRouter initialization failed: {e}")

# Log AI service status
AI_AVAILABLE = GEMINI_AVAILABLE or OPENROUTER_AVAILABLE

if AI_AVAILABLE:
    if GEMINI_AVAILABLE:
        logger.info("AI Service Ready: Gemini 2.0 Flash (Primary)")
    else:
        logger.info("AI Service Ready: OpenRouter (Fallback Only)")
else:
    logger.warning("No AI service available - using static responses")


class AIConversationHandler:
    """
    Simplified AI conversation handler

    Focuses on chat and vehicle search only
    """

    def __init__(self):
        self.system_prompt = """Sen bir elektrikli araç (EV) uzmanı AI asistanısın. 
Kullanıcılara elektrikli araç konularında yardım ediyorsun:
- Rota planlama ve şarj istasyonu önerileri
- EV modelleri ve karşılaştırmaları  
- Şarj teknolojileri ve ipuçları
- Elektrikli araç kullanım önerileri

Türkçe olarak cevap ver, yardımsever ve bilgilendirici ol."""

    async def chat_with_context(self, user_message: str, context: dict):
        """
        Chat with AI including vehicle and charging station context

        Args:
            user_message: User's question
            context: Dict with vehicles, charging_stations, total_vehicles, total_stations
        """
        try:
            # Prepare context summary for AI
            vehicles = context.get("vehicles", [])[:20]  # Top 20 vehicles
            stations = context.get("charging_stations", [])

            # Create vehicle summary
            vehicle_summary = "\n🚗 Mevcut Elektrikli Araçlar (Menzile Göre Sıralı):\n"
            for i, v in enumerate(vehicles, 1):
                vehicle_summary += (
                    f"{i}. {v.get('manufacturer')} {v.get('model')} ({v.get('year')})\n"
                )
                vehicle_summary += f"   • Menzil: {v.get('range_km', 'N/A')} km\n"
                vehicle_summary += (
                    f"   • Batarya: {v.get('battery_capacity_kwh', 'N/A')} kWh\n"
                )
                vehicle_summary += (
                    f"   • Şarj Hızı: {v.get('charge_speed_kwh', 'N/A')} kW\n"
                )

            # Create charging station summary by city
            station_cities = {}
            for station in stations:
                city = station.get("city", "Bilinmeyen")
                if city not in station_cities:
                    station_cities[city] = []
                station_cities[city].append(station)

            station_summary = "\n⚡ Türkiye'deki Şarj İstasyonları:\n"
            for city, city_stations in sorted(station_cities.items()):
                station_summary += f"• {city}: {len(city_stations)} istasyon\n"

            # Enhanced system prompt with context
            enhanced_prompt = f"""{self.system_prompt}

📊 SİSTEM BİLGİSİ:
{vehicle_summary}

{station_summary}

Toplam Araç: {context.get("total_vehicles", 0)}
Toplam Şarj İstasyonu: {context.get("total_stations", 0)}

KONUŞMA TARZI:
- Samimi ve doğal konuş, robot gibi olma
- Kısa ve öz cevaplar ver (2-3 cümle yeterli)
- Gereksiz açıklamalar yapma
- Emoji kullan ama abartma (sadece 1-2 tane)
- Dostça ama profesyonel ol

ÖNEMLİ KURALLAR:
1. Rota sorusu gelirse → SADECE "Hangi aracı kullanıyorsun?" diye sor, başka bir şey söyleme
2. Araç söylendikten sonra → Yukarıdaki listeden menzili bul ve hızlıca hesapla
3. Hesaplama: Şarj sayısı = (Mesafe ÷ (Menzil × 0.8)) yuvarla
4. Mesafeler: İstanbul-Erzurum 1637km, İstanbul-Ankara 450km, Ankara-Sivas 420km
5. Araç söylemeden ASLA kesin sayı verme

Örnek konuşma:
❌ KÖTÜ: "Merhaba! Size yardımcı olmaktan mutluluk duyarım. Öncelikle hangi elektrikli araç modelini kullandığınızı öğrenebilir miyim? Bu bilgi çok önemli..."
İYİ: "Hangi elektrikli aracı kullanıyorsun?"

❌ KÖTÜ: "Tesla Model 3'ünüz 580 km menzile sahiptir. Güvenli kullanım için 0.8 katsayısı uyguladığımızda..."  
İYİ: "Tesla Model 3 ile İstanbul-Ankara arası 1 şarj durağı yeterli!"
"""

            # Try Gemini first
            if GEMINI_AVAILABLE and gemini_model:
                try:
                    chat = gemini_model.start_chat(history=[])
                    response = chat.send_message(
                        f"{enhanced_prompt}\n\n🙋 Kullanıcı Sorusu: {user_message}"
                    )

                    return {
                        "user_message": user_message,
                        "ai_response": response.text,
                        "model_used": "gemini-2.0-flash-exp",
                        "provider": "Google Gemini",
                        "context_used": True,
                        "vehicles_count": len(vehicles),
                        "stations_count": len(stations),
                    }
                except Exception as gemini_error:
                    logger.error(f"❌ Gemini error: {str(gemini_error)}")
                    # Fall back to OpenRouter

            # Fallback to OpenRouter
            if OPENROUTER_AVAILABLE and openrouter_client:
                try:
                    completion = openrouter_client.chat.completions.create(
                        extra_headers={
                            "HTTP-Referer": "https://ev-navigation.local",
                            "X-Title": "EV Navigation Assistant",
                        },
                        model="nvidia/llama-3.1-nemotron-70b-instruct",
                        messages=[
                            {"role": "system", "content": enhanced_prompt},
                            {"role": "user", "content": user_message},
                        ],
                    )

                    return {
                        "user_message": user_message,
                        "ai_response": completion.choices[0].message.content,
                        "model_used": "nvidia/llama-3.1-nemotron-70b-instruct",
                        "provider": "OpenRouter (Fallback)",
                        "context_used": True,
                        "vehicles_count": len(vehicles),
                        "stations_count": len(stations),
                    }
                except Exception as openrouter_error:
                    logger.error(f"❌ OpenRouter error: {str(openrouter_error)}")

            # Both failed
            return {
                "user_message": user_message,
                "ai_response": "Üzgünüm, şu anda AI servislerine erişemiyorum. Lütfen daha sonra tekrar deneyin.",
                "model_used": "none",
                "provider": "Error",
                "context_used": False,
            }

        except Exception as e:
            logger.error(f"❌ Chat with context error: {str(e)}")
            return {
                "user_message": user_message,
                "ai_response": f"Bir hata oluştu: {str(e)}",
                "model_used": "none",
                "provider": "Error",
                "context_used": False,
            }

    async def chat_with_user(self, user_message: str):
        """
        Original chat method (kept for backwards compatibility).

        Smart AI chat with Gemini (Primary) + OpenRouter (Fallback)

        Args:
            user_message: User message

        Returns:
            AI response with model info
        """
        # Call new method with empty context
        return await self.chat_with_context(
            user_message,
            {
                "vehicles": [],
                "charging_stations": [],
                "total_vehicles": 0,
                "total_stations": 0,
            },
        )

    async def handleConversation(self, user_message: str):
        """Alias for chat_with_user for backwards compatibility."""
        return await self.chat_with_user(user_message)

    async def smart_vehicle_search(
        self, query: str, vehicles: List[Dict]
    ) -> Dict[str, Any]:
        """
        Smart vehicle search using Gemini AI (Primary) or OpenRouter (Fallback)

        Args:
            query: User search query
            vehicles: List of available vehicles

        Returns:
            AI-enhanced search results
        """
        try:
            # Create vehicle summary for AI
            vehicle_summary = []
            for i, vehicle in enumerate(vehicles[:20]):
                summary = f"{i + 1}. {vehicle.get('make', '')} {vehicle.get('model', '')} - Menzil: {vehicle.get('range_km', 'N/A')}km, Fiyat: {vehicle.get('base_price_eur', 'N/A')}€"
                vehicle_summary.append(summary)

            vehicles_text = "\n".join(vehicle_summary)

            prompt = f"""Sen bir elektrikli araç uzmanısın. Kullanıcının isteğine en uygun araçları bul.

Mevcut araçlar:
{vehicles_text}

Kullanıcının isteği: {query}

En uygun 3-5 aracı öner ve her biri için kısa açıklama yap. Neden uygun olduklarını belirt."""

            # Try Gemini first
            if GEMINI_AVAILABLE and gemini_model:
                try:
                    response = gemini_model.generate_content(prompt)

                    logger.info("Gemini vehicle search completed")
                    return {
                        "query": query,
                        "ai_recommendations": response.text,
                        "recommended_vehicles": vehicles[:5],
                        "total_available": len(vehicles),
                        "search_type": "gemini_ai_enhanced",
                        "provider": "Google Gemini",
                    }

                except Exception as gemini_error:
                    logger.warning(
                        f"Gemini search failed, trying OpenRouter: {gemini_error}"
                    )

            # Fallback to OpenRouter
            if OPENROUTER_AVAILABLE and openrouter_client:
                try:
                    response = openrouter_client.chat.completions.create(
                        extra_headers={
                            "HTTP-Referer": "https://ev-navigation.local",
                            "X-Title": "EV Navigation Assistant",
                        },
                        model="nvidia/nemotron-nano-9b-v2:free",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                        temperature=0.3,
                    )

                    logger.info("OpenRouter vehicle search completed (fallback)")
                    return {
                        "query": query,
                        "ai_recommendations": response.choices[0].message.content,
                        "recommended_vehicles": vehicles[:5],
                        "total_available": len(vehicles),
                        "search_type": "openrouter_ai_enhanced",
                        "provider": "OpenRouter (Fallback)",
                    }

                except Exception as openrouter_error:
                    logger.error(f"OpenRouter search also failed: {openrouter_error}")

            # Final fallback - simple text search
            logger.warning("All AI providers failed, using text search")
            filtered_vehicles = [
                v for v in vehicles if query.lower() in str(v).lower()
            ][:5]
            return {
                "query": query,
                "results": filtered_vehicles,
                "total_found": len(filtered_vehicles),
                "search_type": "text_fallback",
                "provider": "Simple Text Search",
                "message": "AI araması kullanılamadı, basit metin araması yapıldı.",
            }

        except Exception as e:
            logger.error(f"Smart vehicle search critical error: {e}")
            filtered_vehicles = [
                v for v in vehicles if query.lower() in str(v).lower()
            ][:5]
            return {
                "query": query,
                "results": filtered_vehicles,
                "total_found": len(filtered_vehicles),
                "search_type": "error_fallback",
                "provider": "Error Fallback",
                "error": str(e),
            }
