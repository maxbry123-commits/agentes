import re
import tempfile
from typing import Optional

from bespokelabs import curator
from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class GeminiOCRConfig(BaseModel):
    pdf_url_column: Optional[str] = "pdf_url"
    output_extraction_column: Optional[str] = "output_extraction"
    page_number_column: Optional[str] = "page_number"


class GeminiOCRMap(CompletionsMap):
    def __init__(self, config: dict):
        config = GeminiOCRConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return None

    def prompt(self, input: dict) -> str:
        """Generate a prompt using the ingredients."""
        prompt = f"""
            Extract all text from this PDF, including all text from images. Example extractions could look like this:
            html><body><table><tr><td>2</td><td>1 1</td><td>1 6</td><td>-14</td></tr><tr><td rowspan="2"></td><td>2 3</td><td>7</td><td>14 0</td></tr><tr><td>1</td><td></td><td></td></tr></table></body></html>  

            Notice that the final sum is zero, telling us that 2 is a zero.  But the nice thing about synthetic division, is that long division, the other coefficients are the coefficients of the quotient polynomial.  

            The Remainder Theorem states that when dividing a polynomial by a factor of the form $(x-a)$ there is a quotient polynomial and a constant remainder.  The remainder is P(a) since $P(x)=(x-a)\cdot Q(x)+r\Rightarrow P(a)=(a-a)Q(a)+r=r.$ .  

            # Miscellaneous Facts;  

            It is obvious in any polynomial that $\mathrm(0)$ is the y-intercept and equally as obvious that $\mathrm(1)$ is the sum of all the coefficients.  

            # Problems:  

            1. Given the cubic polynomial $P(x)=x^-7x^-4x+28$ .  Two of the zeros are additive inverses.  Find the zeros.   
            3. If $\mathrm(\mathbf)$ is a polynomial with rational coefficients and roots at 0, 1, $\sqrt$ , and $1-(\sqrt(3))$ , then the degree of $\mathfrak(p)(\ensuremath(\mathbf(x)))$ is at least?   
            4. When Madison's dog chewed up her mathematics assignment, one particular equation was ripped apart.  I found a piece of the beginning of the equation and a piece at the end, but the middle was missing.  The beginning piece was $x^(5)-9x^(4)+$ and the ending piece was $+11=0$ .  Fortunately the teacher had promised that all of the roots would be integers.  How many times is $^(-1)$ a root? [Furman ????]   
            5. The following is a polynomial.  Find the sum of the squares of its coefficients. $\sqrt[3](x^(9)-3x^(8)+18x^(7)-28x^(6)+84x^(5)-42x^(4)+98x^(3)+72x^+15x+1)$ .  FURMAN   
            6. If a cubic polynomial $\operatorname(p)(\mathbf(x))$ has roots at -1, 2, and 3, and if $\mathfrak(p)(0)=1$ , then the remainder when $\mathfrak(p)(\ensuremath(\mathbf(x)))$ is divided by $\mathbf(X)-1$ is:   
            7. If 2 is a solution of $x^(3)+h x+10=0$ , then h equals:   
            8. The number of distinct real solutions of the equation $4x^(3)-8x^(2)+5x-1=0$ is:   
            9. What is the sum of the squares of the roots of $x^(4)-5x^(2)+6=0$   
            10. For how many integers $_\mathrm(N)$ is $N^(4)+6N<6N^(3)+N^(2)?$   
            11. How any times does the graph of $f(x)=x^(3)-x^(2)+2x+4$ cross the $\mathbf(X)$ axis?   
            12. Madison's dog chewed on her homework before she could finish it.  The fragment saved from the horrible canine's mouth reveal only the two terms of highest degree of the polynomial $\mathfrak(p)(\ensuremath\mathbf(x)))

            Now please give me your extraction of all text, including text in images.
        """
        pdf_bytes = input["page_bytes"]
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(pdf_bytes)
        tmp.close()
        return prompt, curator.types.File(url=tmp.name)

    def parse(self, input: dict, response: str) -> dict:
        """Parse the model response along with the input to the model into the desired output format.."""
        return {
            **input,
            self.config.output_extraction_column: response,
        }
