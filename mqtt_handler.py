from fastapi_mqtt import FastMQTT, MQTTConfig
import json
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

# --- MQTT Configuration ---
mqtt_config = MQTTConfig(
    host="broker.hivemq.com",
    port=1883,
    keepalive=60,
    version=4  # MQTT v3.1.1
)
mqtt = FastMQTT(config=mqtt_config)


@mqtt.on_connect()
def connect(client, flags, rc, properties):
    """Called when MQTT connects to broker"""
    print("=" * 60)
    print("✅ MQTT CONNECTED to broker.hivemq.com")
    print("=" * 60)
    
    # Subscribe to the car counts topic
    mqtt.client.subscribe("flextraff/car_counts", qos=1)
    print("📡 Subscribed to topic: flextraff/car_counts")
    print("🎧 Listening for messages from Raspberry Pi...\n")


@mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    """Called when MQTT disconnects"""
    print("⚠️ MQTT Disconnected from broker")


@mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    """Called when subscription is confirmed"""
    print(f"✅ Subscription confirmed (mid={mid}, qos={qos})")


@mqtt.on_message()
async def message_handler(client, topic, payload, qos, properties):
    """
    Main message handler - receives car counts from Pi
    and sends back calculated green times
    """
    print("\n" + "=" * 60)
    print(f"📩 MQTT MESSAGE RECEIVED on topic: {topic}")
    print("=" * 60)

    try:
        # Decode the payload
        data = json.loads(payload.decode())
        print(f"📥 Car count data from Pi: {data}")
        
        lane_counts = data.get("lane_counts", [])
        junction_id = data.get("junction_id", 1)
        
        print(f"🚗 Lane counts: {lane_counts}")
        print(f"🚦 Junction ID: {junction_id}")

        # Call FastAPI endpoint to calculate timing
        print("\n📤 Calling FastAPI /calculate-timing endpoint...")
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.post(
                    "http://localhost:8001/calculate-timing",
                    json=data
                )
                
                print(f"📊 FastAPI Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Calculated green times: {result.get('green_times')}")
                    print(f"⏱️  Total cycle time: {result.get('cycle_time')}s")
                    
                    # Publish green times back to Pi
                    green_times_payload = json.dumps({
                        "green_times": result.get("green_times"),
                        "cycle_time": result.get("cycle_time"),
                        "junction_id": junction_id
                    })
                    
                    mqtt.client.publish(
                        "flextraff/green_times", 
                        green_times_payload,
                        qos=1,
                        retain=False
                    )
                    
                    print(f"📡 Published green times to Pi on topic: flextraff/green_times")
                    print(f"✅ MQTT message processing complete\n")
                    
                else:
                    print(f"❌ FastAPI returned error {response.status_code}: {response.text}")
                    
            except httpx.TimeoutException:
                print("❌ FastAPI request timed out after 30 seconds")
            except httpx.ConnectError:
                print("❌ Could not connect to FastAPI at http://localhost:8001")
            except Exception as e:
                print(f"❌ Error calling FastAPI: {type(e).__name__}: {e}")

    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON payload: {e}")
        print(f"   Raw payload: {payload}")
    except Exception as e:
        print(f"❌ MQTT message handler error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


# Export the mqtt instance
__all__ = ['mqtt']