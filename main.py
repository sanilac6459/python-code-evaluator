# imported the libraries and modules [FROM Jupyter Notebook]
import openai
import os
import httpx
import inspect
from typing import Any, Mapping
import logging
import asyncio
import uuid
from dataclasses import dataclass, field 

# using all the required functions [FROM Jupyter Notebook]
from openai.types.chat import (
    ChatCompletionMessageParam, ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam
)

_framework_log = logging.getLogger('permai.util')

openai.api_key = os.getenv('OPENAI_KEY')

@dataclass
class GenerationResponse():
    text: str
    model: str
    task: str
    prompt_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    failure_reason: str | None = None
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()), repr=False)

    def __post_init__(self):
        """
        mypy will catch most typing errors, but objects which may get loaded from files
        may need additional validation. also colab doesn't really do mypy, so some
        extra validation is nice. __post_init__ is a handy dunder method for running
        validations on dataclasses without messing with the default __init__ method,
        which can get messy, to say the least.
        """
        for fkey in ['text', 'model', 'task', 'prompt_id']:
            if not isinstance(getattr(self, fkey), str):
                raise ValueError(f'{fkey} field expected string, got {getattr(self, fkey)}')

        for fkey in ['input_tokens', 'output_tokens']:
            if (fv := getattr(self, fkey)) and not isinstance(fv, int):
                raise ValueError(f'{fkey} field expected int, got {fv}')

        for fkey in ['failure_reason', 'response_id']:
            if (fv := getattr(self, fkey)) and not isinstance(fv, str):
                raise ValueError(f'{fkey} field expected str, got {fv}')
            
def openai_dicts_to_message_params(messages: list[dict[str, str]]) -> list[ChatCompletionMessageParam]:
    foo: list[ChatCompletionMessageParam] = []

    for m in messages:
        if m['role'] == 'system':
            foo.append(ChatCompletionSystemMessageParam(content=m['content'], role='system'))
        elif m['role'] == 'user':
            foo.append(ChatCompletionUserMessageParam(content=m['content'], role='user'))
        elif m['role'] == 'assistant':
            foo.append(ChatCompletionAssistantMessageParam(content=m['content'], role='assistant'))
        else:
            raise ValueError(f'unknown role {m["role"]}')

    return foo


async def call_openai_compat_with_retries(
        model: str,
        messages: list[dict[str, str]],
        client: openai.AsyncOpenAI,
        provider_name: str = 'openai',
        max_retry: int = 10,
        n: int = 1,  # NOTE: only for openai usage
        model_parameters: Mapping[str, Any] | None = None,
        *,
        prompt_id: str = 'adhoc',
        task: str = 'default',
        raise_exceptions=False,
        quiet: bool = False) -> list[GenerationResponse]:
    """
    This is the real function that gets used for calling OpenAI. Highly recommend
    using n=3 rather than n=1.
    """
    if model_parameters is None:
        model_parameters = {}

    local_logger = _framework_log.info
    if quiet:
        local_logger = _framework_log.debug

    message_params = openai_dicts_to_message_params(messages)
    _framework_log.debug(f'Using model {model}, {n} generations')
    attempts = 0
    response = None

    # some parameters from togetherai have to be passed as 'extra body' as the openai
    # client library does not support them directly on the completions API
    funcsig = inspect.signature(client.chat.completions.create)
    openai_params = {
        k: v for k, v in model_parameters.items() if k in funcsig.parameters
    }
    extra_body = {
        k: v for k, v in model_parameters.items() if k not in funcsig.parameters
    }

    while attempts < max_retry:
        try:
            attempts += 1
            response = await client.chat.completions.create(
                messages=message_params,
                model=model,
                timeout=120,
                n=n,
                extra_body=extra_body,
                **openai_params,
            )
          
            
            break
        except openai.RateLimitError:
         
            _framework_log.info(f'openai.RateLimitError...Retrying in {10 * attempts} seconds')
            await asyncio.sleep(10 * attempts)
        except openai.APITimeoutError:
            
            _framework_log.info(f'openai.Timeout...Retrying in {2 * attempts} seconds')
            await asyncio.sleep(2 * attempts)
        except openai.APIConnectionError:
          
            _framework_log.info(f'openai.APIConnectionError...Retrying in {2 * attempts} seconds')
            await asyncio.sleep(2 * attempts)
        except openai.APIError as exc:
          
            _framework_log.warning(f'Unretryable error: openai.APIError error content is {str(exc)}', exc_info=exc)
            break
        except TimeoutError:
           
            _framework_log.info(f'TimeoutError...Retrying in {2 * attempts} seconds')
            await asyncio.sleep(2 * attempts)
        except httpx.ReadTimeout:
        
            _framework_log.info(f'httpx TimeoutError...Retrying in {2 * attempts} seconds')
            await asyncio.sleep(2 * attempts)
        except Exception as exc:
           
            _framework_log.warning(f'Unhandled exception type raised: {exc}', exc_info=exc)
            _framework_log.warning('Giving up since this is unexpected.')
            break

    if response is None and raise_exceptions:
        raise RuntimeError(f'{provider_name} calls failed after {max_retry} attempts.')
    elif response is None:
        _framework_log.error('Failed to generate a response, but not raising an exception.')
    else:
        _framework_log.debug(response.choices)
        avg_output_tokens = response.usage.completion_tokens // len(response.choices)
        return [GenerationResponse(
            text=choice.message.content,
            model=model,
            task=task,
            prompt_id=prompt_id,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=avg_output_tokens)
                for choice in response.choices]
    return []

OPENAI_CLIENT: openai.AsyncOpenAI | None = None

def init_openai(openai_key: str | None = None) -> openai.AsyncOpenAI:
    
    global OPENAI_CLIENT
    if not OPENAI_CLIENT:
        openai_key = openai_key or os.getenv('OPENAI_KEY')
        OPENAI_CLIENT = openai.AsyncOpenAI(api_key=openai_key)

    return OPENAI_CLIENT

def get_openai_client() -> openai.AsyncOpenAI:
    return init_openai()



# MAIN FUNCTIONALITY BEGINS HERE

# function to identify the programming language of user code
async def identify_language(user_code):
    client = get_openai_client()
    user_message = user_code
    model = 'gpt-4o' 

    responses = await call_openai_compat_with_retries(
        model = model,
        messages = [
            {'role': 'system', 'content': 'Identify the programming language of this code. Only provide the language, not a complete sentence'},
            {'role': 'user', 'content': user_message},],
        client = client,
    )
    return responses[0].text.strip().capitalize()

# function to check if user code is pythonic or not
async def is_code_pythonic(user_code):
    client = get_openai_client()
    user_message = user_code
    model = 'gpt-4o' 

    responses = await call_openai_compat_with_retries(
        model = model,
        messages = [
            {'role': 'system', 'content': """Analyze the following Python code and determine \
             whether it is Pythonic. Respond with "Yes" or "No" \
            followed by a brief explanation. If the code is not Pythonic, explain why and provide suggestions in bullet points and labeled it 'Suggestions'. \
             Please do not provide the more Pythonic version of the code yet.""",
            },
            {'role': 'user', 'content': user_message},],
        client = client,
    )
    return responses[0].text.strip().capitalize()

# function to generate more pythonic version of user code
async def more_pythonic_code(user_code):
    client = get_openai_client()
    user_message = user_code
    model = 'gpt-4o' 

    responses = await call_openai_compat_with_retries(
        model = model,
        messages = [
            {'role': 'system', 'content': """Rewrite the user code in more Pythonic way first, no explaination. Then \
             provide a brief explanation of why it's more preferable.""",
            },
            {'role': 'user', 'content': user_message},],
        client = client,
    )
    return responses[0].text.strip().capitalize()
    

async def compare_outputs(user_code, pythonic_code):
    client = get_openai_client()
    model = 'gpt-4o' 

    responses = await call_openai_compat_with_retries(
        model = model,
        messages = [
            {'role': 'system', 'content': """Compare the outputs between the user's provided code and the more Pythonic version \
             of the code with no explaination first. Then explain the similarities and differences (if any) between the two outputs.""",
            },
            {'role': 'user', 'content': f"User Code:\n{user_code}\n\nPythonic Code:\n{pythonic_code}"},],
        client = client,
    )
    return responses[0].text.strip().capitalize()


async def main():
    language = None 
    while language != 'python': 
        # ensure the user enters Python code
        try:
            user_code = input("Please enter a Python code: ")
            language = await identify_language(user_code)
            language = language.capitalize().strip()

            if language != 'Python': 
                print("\n")
                print("This is not Python code, please enter a Python code.")
            
            # goes onto to analyzing how Pythonic the code is
            else:
                print("\n")
                print("Thank you for providing Python code. Please wait...")
                print("\n")
                pythonic_analysis = await is_code_pythonic(user_code)
                pythonic_analysis = str(pythonic_analysis).strip() 
                print(f"Is the code Pythonic or not: {pythonic_analysis}")

                # if user code is already Pythonic, no need for the evaluator to continue
                if pythonic_analysis.capitalize().startswith('Yes'):
                    print("\n")
                    print("Your code is already Pythonic!")
                    break
                else:
                    # provide more Pythonic version depending on user's choice and the outputs between the two
                    print("\n")
                    user_choice = input("Would you like to see the more Pythonic version of your code and the output between the two? (y/n): ").strip().lower()
                    if user_choice == 'y':
                        pythonic_version = await more_pythonic_code(user_code)
                        print("\n")
                        print("Here's the more Pythonic version of your code:")
                        print(pythonic_version)

                        comparison_result = await compare_outputs(user_code, pythonic_version)
                        print("\n")
                        print("Comparing the outputs:")
                        print("\n")
                        print(comparison_result)
                        
                    # user rather not see the more Pythonic version
                    else:
                        print("\n")
                        print("Okay, I hope the suggestions help! Goodbye!")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break


if __name__ == "__main__":
    asyncio.run(main())

