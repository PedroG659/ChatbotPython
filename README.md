# Envio Automático pelo WhatsApp

Este script em Python automatiza o envio de mensagens de cobrança pelo WhatsApp Web, utilizando dados de clientes armazenados em uma planilha do Excel.

## Pré-requisitos

Antes de executar o script, certifique-se de ter os seguintes requisitos instalados:

* **Python 3.x:** Certifique-se de que o Python esteja instalado em seu sistema. Você pode baixá-lo em [python.org](https://www.python.org/).
* **Bibliotecas Python:** Instale as bibliotecas necessárias usando o pip:

    ```bash
    pip install openpyxl pyautogui
    ```

* **Arquivo Excel:** Crie um arquivo Excel chamado `clientes.xlsx` com os dados dos clientes. A planilha deve ter o seguinte formato:

    | Nome  | Telefone    | Vencimento |
    | ----- | ----------- | ---------- |
    | João  | 55119999999 | 2024-12-31 |
    | Maria | 55218888888 | 2024-12-25 |
    | ...   | ...         | ...        |

    * **Nome:** Nome do cliente.
    * **Telefone:** Número de telefone do cliente com o código do país e DDD (ex: 55119999999).
    * **Vencimento:** Data de vencimento no formato AAAA-MM-DD.

* **Imagem do Botão de Envio:** Capture uma imagem do botão de envio do WhatsApp Web e salve-a como `seta.png` na mesma pasta do script.

## Como Usar

1.  **Prepare o ambiente:**
    * Instale o Python e as bibliotecas necessárias.
    * Crie o arquivo `clientes.xlsx` com os dados dos clientes.
    * Salve a imagem do botão de envio do WhatsApp Web como `seta.png`.

2.  **Execute o script:**
    * Abra um terminal ou prompt de comando.
    * Navegue até a pasta onde o script está localizado.
    * Execute o script Python:

        ```bash
        python seu_script.py
        ```

3.  **Acompanhe o processo:**
    * O script abrirá o WhatsApp Web no seu navegador padrão.
    * Após o carregamento, ele começará a enviar as mensagens de cobrança para cada cliente na planilha.
    * Se ocorrer algum erro no envio de uma mensagem, o nome e o telefone do cliente serão registrados no arquivo `erros.csv`.

## Observações Importantes

* **Tempo de Espera:** O script utiliza `sleep()` para aguardar o carregamento das páginas e a execução das ações. Ajuste os valores de tempo de espera se necessário, dependendo da velocidade da sua conexão com a internet e do desempenho do seu computador.
* **Formato do Número de Telefone:** Certifique-se de que os números de telefone na planilha estejam no formato correto (com o código do país e o DDD).
* **Imagem do Botão de Envio:** A imagem `seta.png` deve corresponder exatamente ao botão de envio do WhatsApp Web. Se o botão mudar de aparência, você precisará capturar uma nova imagem.
* **Tratamento de Erros:** O script inclui um bloco `try...except` para lidar com erros durante o envio das mensagens. Verifique o arquivo `erros.csv` para identificar os clientes para os quais o envio falhou.
* **Segurança:** O uso de `pyautogui` para controlar o navegador pode ser arriscado se você estiver usando o computador para outras tarefas ao mesmo tempo. Considere usar bibliotecas como `selenium` para um controle mais preciso do navegador, se preferir.
* **Uso Responsável:** O envio em massa de mensagens pelo WhatsApp Web pode violar os termos de serviço do WhatsApp e resultar no bloqueio da sua conta. Use esta ferramenta com responsabilidade.