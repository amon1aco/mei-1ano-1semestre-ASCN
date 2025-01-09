# 22.04 
FROM ubuntu:22.04

# frontend não-interativo evita prompts durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# dependencias
RUN apt-get update && apt-get install -y \
    python3-pip \  
    libpq-dev \  
    build-essential \  
    python3-dev \  
    curl \  
    && apt-get clean  

# diretoria
WORKDIR /app

# copiar requirements
COPY codebase/moonshot/requirements.txt /app/

# instalar requirements.txt
RUN pip install --no-cache-dir -r requirements.txt  

# copiar moonshot 
COPY codebase/moonshot /app/

# Expor a porta 8000
EXPOSE 8000

# copiar o script para o container
COPY moonshotscript.sh /app/

# garantir permissão de execução
RUN chmod +x /app/moonshotscript.sh

# executar
CMD ["/app/moonshotscript.sh"]
