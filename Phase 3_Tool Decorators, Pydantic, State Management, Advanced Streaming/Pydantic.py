from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, List
import json


# ============= DEFINE YOUR DATA MODELS =============
class WeatherInfo(BaseModel):
    """Structure for weather data."""
    city: str = Field(..., description="City name", min_length=1)
    temperature: float = Field(..., description="Temperature in Fahrenheit", ge=-100, le=150)
    condition: str = Field(default="unknown", description="Weather condition")
    humidity: Optional[int] = Field(None, description="Humidity percentage", ge=0, le=100)

    @field_validator('city')
    def city_must_be_valid(cls, v):
        """Custom validation."""
        if v.lower() in ['nowhere', 'unknown']:
            raise ValueError('City cannot be "nowhere" or "unknown"')
        return v.title()  # Capitalize first letter


class EmailAction(BaseModel):
    """Structure for email sending action."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line", max_length=100)
    body: str = Field(..., description="Email body content")
    priority: str = Field(default="normal", description="Priority: low, normal, high")

    @field_validator('to')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError(f'Invalid email address: {v}')
        return v


class AgentResponse(BaseModel):
    """What your agent returns to the user."""
    action: str = Field(..., description="Action taken: weather, email, chat, search")
    success: bool = Field(..., description="Whether action succeeded")
    message: str = Field(..., description="Response message for user")
    data: Optional[dict] = Field(None, description="Optional extra data")


# ============= USING PYDANTIC WITH LLM =============
def extract_structured_data(llm_output: str, model_class: BaseModel):
    """
    Tell LLM to return JSON that matches our Pydantic model.
    Then validate it automatically.
    """
    # Step 1: Get LLM output (pretend this is from OpenAI)
    # In production, you'd have a prompt that says "Return JSON matching this schema"

    try:
        # Step 2: Parse JSON
        if isinstance(llm_output, str):
            data = json.loads(llm_output)
        else:
            data = llm_output

        # Step 3: Validate with Pydantic (THIS IS THE MAGIC)
        validated = model_class(**data)

        return validated

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None
    except ValidationError as e:
        print(f"❌ Validation failed: {e}")
        print(f"   Errors: {e.errors()}")
        return None


# ============= DEMO =============
print("=" * 60)
print("PYDANTIC VALIDATION DEMO")
print("=" * 60)

# Valid weather data
valid_weather = '{"city": "tokyo", "temperature": 72, "condition": "sunny", "humidity": 65}'
result = extract_structured_data(valid_weather, WeatherInfo)
if result:
    print(f"✅ Valid weather: {result.city}, {result.temperature}°F, {result.condition}")
    print(f"   (auto-capitalized city: {result.city})")

print()

# Invalid weather data (temperature out of range)
invalid_temp = '{"city": "london", "temperature": 500, "condition": "hot"}'
result = extract_structured_data(invalid_temp, WeatherInfo)
if not result:
    print("❌ Temperature 500°F rejected (must be between -100 and 150)")

print()

# Invalid email
invalid_email = '{"to": "notanemail", "subject": "Hello", "body": "Hi there"}'
result = extract_structured_data(invalid_email, EmailAction)
if not result:
    print("❌ Invalid email address rejected")


#Invalid email (missing @)
invalid_email = '{"to": "userexample.com", "subject": "Hello", "body": "Hi there"}'
result = extract_structured_data(invalid_email, EmailAction)

#Invalid email (missing .)
invalid_email = '{"to": "user@example", "subject": "Hello", "body": "Hi there"}'
result = extract_structured_data(invalid_email, EmailAction)


# Valid email
valid_email = '{"to": "user@example.com", "subject": "Meeting", "body": "Let\'s sync at 2pm"}'
result = extract_structured_data(valid_email, EmailAction)
if result:
    print(f"✅ Valid email: to={result.to}, subject={result.subject}")
    print(f"   (capitalized email: {result.to})")
    print(f"   (auto-capitalized subject: {result.subject})")
    print(f"   (auto-capitalized body: {result.body[:10]}...)")
    print(f"   (auto-capitalized priority: {result.priority})")
    print()
else:
        print("❌ Email validation failed")


