# ⛓️ Guía de Despliegue Blockchain (Polygon)

Para que el sistema de $DULCE deje de ser una simulación y viva en la "red real", sigue estos pasos para desplegar tu Contrato Inteligente.

## 1. Conexión a la Red (Amoy Testnet)
Antes de gastar dinero real, usaremos la red de pruebas **Amoy** de Polygon.

1. Abre tu billetera **MetaMask**.
2. Ve a [Polygon Amoy Faucet](https://faucet.polygon.technology/) y pide algunos tokens **MATIC** de prueba para pagar el gas.
3. Asegúrate de que tu red en MetaMask sea "Polygon Amoy".

## 2. Despliegue con Remix IDE
No necesitas instalar nada en tu computadora.

1. Ve a [remix.ethereum.org](https://remix.ethereum.org).
2. Crea un archivo nuevo llamado `DulceToken.sol`.
3. Copia y pega el código que dejé en `contracts/DulceToken.sol`.
4. En la pestaña **Solidity Compiler**, dale al botón "Compile DulceToken.sol" (usa versión 0.8.20+).
5. En la pestaña **Deploy & Run Transactions**:
   - Cambia "Environment" a **Injected Provider - MetaMask**.
   - Asegúrate de que diga "DulceToken" en el selector de contratos.
   - Haz clic en **Deploy**.
   - Confirma la transacción en MetaMask.

## 3. Configuración en la App
Una vez desplegado, Remix te dará una dirección (ej: `0x123...`).

1. Abre `src/lib/web3.ts`.
2. Reemplaza `DULCE_TOKEN_ADDRESS` con tu nueva dirección.
3. ¡Listo! Tu web ahora leerá los balances reales de la Blockchain.

## 4. Integración con Worldcoin (World ID)
Para asegurar que cada "Dulce Regalo" llegue a una persona real y no a un bot, integramos Worldcoin.

### ¿Qué es?
Es un sistema de **Prueba de Personhood (PoP)**. Permite que el cliente demuestre que es humano sin revelar su nombre o cara.

### Cómo activarlo:
1. Regístrate en [developer.worldcoin.org](https://developer.worldcoin.org).
2. Crea una "Action" llamada `verify-human-customer`.
3. ✅ `app_id` configurado: `app_f46e5db6f7c46cfaa400aefc65f52c99`.

### Beneficio para Dulces Momentos:
- **Adiós al fraude**: Evita que una persona use 100 correos para obtener 100 cupones de descuento.
- **Exclusividad**: Solo humanos verificados pueden reclamar los NFTs de "Fundador Dulce".
- **Privacidad**: No guardamos datos personales, solo una confirmación matemática de que el cliente es único.

---
**Nota:** Para "Mintear" (dar puntos) a los clientes de forma automática, necesitarás que el backend (o tú mismo desde Remix) llame a la función `rewardPoints`.
