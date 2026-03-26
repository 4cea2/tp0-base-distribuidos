# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

 El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de:  **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target  | accion  |
|---|---|
|  `docker-compose-up`  | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers. |
| `docker-compose-down`  | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego  `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
|  `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |
| `docker-image`  | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto. |
| `build` | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_. |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar. 

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.


### Cliente
 se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:
 
1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up`  y luego  `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.  El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc. 

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).


### Ejercicio N°3:
Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `


### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.



#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).


### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). 
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del *batch* fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB. 

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
 (hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. 

El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación.  Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados  [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
Respetar el formato y contenido las entradas de logs descritas en los ejercicios, pues son las que se chequean en cada uno de los tests.

# Resolucion

## Ejercicio 1

Para crear el `.sh`, opté por tener un subscript en Python que usa el mismo `.sh`.

Este `.sh`, que lo podemos pensar como un *wrapper*, recibe como parámetro el nombre del archivo final y la cantidad de clientes a generar. Luego, invoca al subscript de Python con los parámetros, el cual generará el archivo indicando los servicios (server y client) y la network.

Cabe mencionar que tomé como ejemplo el `.sh` que daban en el enunciado.

## Ejercicio 2

Se inyectan los *configs* en el generador de Python a través de *Docker volumes*, más específicamente del tipo **bind mount**, ya que queremos que los cambios que hagamos a nivel *host* sobre los *configs* se vean reflejados directamente cuando corren los contenedores. De esta manera, la configuración queda persistida por fuera de la imagen.

También eliminé los log level que venían en el docker-compose, porque en los *configs* ya están definidos.

## Ejercicio 3

Para crear el `.sh`, utilicé una imagen de Docker (*Alpine*), la cual incluye `sh` y el comando `netcat`.

Dentro del script, se levanta un contenedor (que luego se cierra por sí mismo con `--rm`) que se comunica con el servidor y envía un mensaje a través de su *network*. Luego, espera recibir una respuesta, que debería ser exactamente la misma que se envió (echo server).

Finalmente, se realiza una verificación comparando el mensaje enviado con el recibido para determinar si el comportamiento del servidor es correcto.

## Ejercicio 4

### Server

Para manejar la señal `SIGTERM`, creé una funcion que, al recibir la señal, intenta cerrar los sockets: tanto el socket que acepta nuevas conexiones como el de la conexión actual con el cliente. Tambien corta el loop principal a traves de un bool (*_is_running*)

Puede darse el caso de que alguno de estos sockets ya haya sido cerrado (ejemplo: la conexión con el cliente ya terminó), por lo que antes de cerrarlos se realiza una verificación para evitar errores.

### Client

En el cliente, utilicé *goroutines* (un thread liviano) junto con un *channel*.

La goroutine se encarga de manejar la señal `SIGTERM` mientras que el cliente continúa comunicándose con el servidor.

Por otro lado, el channel se usa como comunicación entre la goroutine y el hilo principal, permitiendo avisar cuándo se debe cortar el loop de envío de mensajes.

Cuando se recibe la señal, se cierra la conexión activa (si existe), se loguea el evento y se notifica al hilo principal para que finalice.

## Ejercicio 5

Tanto para el server como para el client, se implemento 2 clases:

- **Socket**: se encarga de enviar y recibir datos entre servidor y cliente, evitando problemas de short read/write.
- **Protocol**: abstrae el uso del socket en el servidor/cliente, de forma tal que no manejen bytes directamente. En su lugar, provee métodos de más alto nivel (como `SendBet` o `receive_bet`). Además, se encarga de serializar y deserializar el bet.

### Server

Modifiqué el loop principal, el cual ahora espera recibir un bet y luego envía la confirmación una vez que este es almacenado mediante `store_bet`.

### Client

Agregué una clase Bet, que se encarga de crearse a partir de las variables de entorno definidas en el generador.

Para construirlo, se leen los valores desde las variables de entorno necesarias. Estas variables son definidas en el generador generador. Inicialmente consideré usar un archivo `.env`, pero como no lo podia subir al repositorio, los tests lo eliminaban automáticamente (ya que se ejecutan sobre el último commit de la branch).

En su creacion, se valida que no haya errores en los campos:
- En los *strings*, se verifica que no estén vacíos.
- En los campos numéricos (como `document` y `number`), se valida que puedan convertirse correctamente a enteros.

Dado que se envia un solo bet, eliminé el loop anterior. El cliente simplemente envia y espera la confirmación.

También eliminé el channel que había implementado previamente, ya que sin loop no es necesario. En caso de  el loop, se interrumpiría al recibir un `SIGTERM`, ya que el socket se cierra y el cliente maneja ese error.

### Comunicación

El flujo de comunicación es el siguiente:

1. El servidor espera conexiones de clientes.
2. El cliente se conecta al servidor.
3. El servidor acepta la conexión y espera recibir el bet.
4. El cliente crea el bet, lo envía y espera la confirmación.
5. El servidor recibe el bet, lo almacena y envía la confirmación.
6. El cliente recibe la confirmación y cierra el socket.
7. El servidor cierra la conexión una vez enviada la confirmación.
8. Vuelve al paso 1

### Serialización

La serialización del bet sigue un formato similar a TLV, con algunas modificaciones:

- **TYPE (1 byte)**:
  - 1 → entero
  - 2 → string

- **LENGTH (2 bytes)**:
  - Solo se utiliza para los campos de tipo *string*

- **VALUE (tamaño dinámico)**:
  - Para enteros: 4 bytes
  - Para strings: longitud variable según el campo *LENGTH*

- **Orden de los campos**:
  Agency → FirstName → LastName → Document → BirthDate → Number

Luego, para la confirmacion, simplemente consta de un solo byte.

### Ejemplo

- `[01][00 00 00 01]` → Agency = 1 (int32)  
- `[02][00 10]Santiago Lionel` → FirstName (longitud = 16)  
- `[02][00 05]Lorca` → LastName (longitud = 5)  
- `[01][01 D7 8F 91]` → Document = 30904465 (int32)  
- `[02][00 0A]1999-03-17` → BirthDate (longitud = 10)  
- `[01][00 00 1D 96]` → Number = 7574 (int32)

## Ejercicio 6

### Client

Se crea un ReaderCsv, encargado de procesar el archivo `.csv` y generar los registros necesarios para construir los bets.

Ahora, el Bet ya no se construye a partir de variables de entorno, sino a partir de cada registro devuelto por el `ReaderCsv`, manteniendo las validaciones sobre sus campos.

En lugar de enviar un único bet, el cliente ahora envía un batch de bets y espera la confirmación del mismo. A medida que procesa cada registro del CSV, va completando el batch. Todo esto ocurre dentro de un loop.

Una vez que envía todos los batches, notifica al servidor que no hay más datos por enviar y cierra la conexión.

El protocolo ahora incluye el método `SendBatch`, que es el equivalente de `receive_batch` del lado del servidor.


### Server

El servidor ahora recibe batches en lugar de bets. A medida que recibe cada batch, intenta almacenarlo y responde con una confirmación indicando si la operación fue exitosa.

Cuando recibe el aviso de que no hay más batches (batch vacío), envía una última confirmación y cierra la conexión con el cliente.

El protocolo incluye el método `receive_batch`, equivalente a `SendBatch` del cliente.


### Comunicación

El flujo de comunicación ahora es iterativo y basado en batches:

1. El servidor espera conexiones de clientes.
2. El cliente se conecta al servidor.
3. El servidor acepta la conexión y espera recibir un batch.
4. El cliente crea un batch, lo envía y espera la confirmación.
5. El servidor recibe el batch, lo almacena y envía la confirmación.
6. El cliente recibe la confirmación.
7. Se repiten los pasos 4–6 hasta enviar todos los batches.
8. El cliente envía un batch vacío para indicar que no hay más datos.
9. El servidor responde con una última confirmación.
10. El cliente cierra la conexión.
11. El servidor cierra la conexión y vuelve a esperar nuevos clientes.


### Serialización

La serialización de un batch tiene la siguiente estructura:

- **Cantidad de bets (4 bytes)**
  - Por defecto, suele ser la maxima cantidad de bets que puede enviar por la red sin que supere los 8kb (100 o menos)

- **N bets**
  - cada uno serializado con el formato definido en el ejercicio 5


La confirmación del servidor consiste en **1 byte**:

- 0 → éxito
- 1 → error

Independientemente del resultado, el cliente continúa enviando batches.

Para indicar que no hay más batches por enviar, el cliente envía un batch con **cantidad de bets igual a 0**. Esto actúa como señal de finalización.

### Calculo del tamaño del batch
Suponemos que estamos en el peor caso, es decir, donde cada campo del bet es lo más largo posible dentro de lo razonable. 

Con esto podemos estimar un tamaño máximo que podría tener un batch.

En funcion de como serializamos cada batch, detallamos el costo en bytes de cada campo:

- **Header del batch** (4 bytes) — Se suma una vez por paquete.
- **Campos del bet**:
   - Agency     (int32): Type (1) + Value (4) = 5 bytes.
   - FirstName (string): Type (1) + Length (2) + Texto. Si estimamos un nombre "largo" de 20 caracteres = 23 bytes.
   - LastName  (string): Type (1) + Length (2) + Texto. Si estimamos un apellido "largo" de 20 caracteres = 23 bytes.
   - Document   (int32): Type (1) + Value (4) = 5 bytes.
   - BirthDate (string): Type (1) + Length (2) + "YYYY-MM-DD" (10) = 13 bytes.
   - Number     (int32): Type (1) + Value (4) = 5 bytes.
   
Total estimado por bet: ~74 bytes.
   
Cada paquete total (Header + Bets) tiene que ser menor a 8000 bytes:
- 8000 bytes (límite) - 4 bytes (header) = 7996 bytes disponibles para bets.
- 7996 bytes / 74 bytes por bet es aprox 108 bets por batch.

Entonces, un tamaño "razonable" para el tamaño del batch podría ser 100 bets por batch, dejando un margen de seguridad para variaciones en el tamaño de los campos.

## Ejercicio 7

### Client

Se realizaron pocos cambios en el cliente, ya que la notificación de finalización (envío de un batch con 0 bets) ya estaba implementada, por lo que esa parte se mantiene igual.

Una vez enviada esta notificación, el cliente realiza una consulta de ganadores, la cual será respondida por el servidor cuando disponga de los resultados. Hasta ese momento, el cliente permanece bloqueado esperando la respuesta.

Cuando recibe los ganadores, el cliente cierra la conexión con el servidor.

### Server

El servidor ahora debe esperar a que todas las agencias se conecten y envíen sus apuestas antes de iniciar el sorteo.

Para esto, acepta conexiones hasta que ocurra alguna de las siguientes condiciones:

- Se reciba una señal `SIGTERM`, o
- Se haya alcanzado la cantidad esperada de clientes (definida mediante una variable de entorno generada en el `.sh`)

Cuando un cliente finaliza el envío de sus apuestas y realiza la consulta de ganadores, el servidor lo mantiene en espera, almacenando su conexión en un diccionario.

Una vez finalizado el sorteo, el servidor recorre estas conexiones en espera y envía los ganadores a cada cliente.

Luego de enviar los resultados, el servidor cierra todas esas conexiones.

### Comunicación

El flujo es similar al del ejercicio anterior, con una extensión al final:

- Luego de recibir la confirmación del batch vacío, el cliente envía una **consulta de ganadores**.
- El cliente queda esperando la respuesta del servidor.
- El servidor recibe esta consulta y mantiene la conexión en espera.
- Cuando el sorteo finaliza, el servidor envía los ganadores a todos los clientes en espera.

### Serialización

- **Consulta de ganadores**: se representa con un byte de valor 3.
- **Respuesta de ganadores**:
  - Sigue un formato similar al de un batch.
  - En lugar de la cantidad de bets, incluye la **cantidad de ganadores**.
  - Luego se envían los bets ganadores (en el fondo son bets).

## Ejercicio 8

Entiendo que al usar multithreading en python, el GIL impide que muchos hilos ejecuten el mismo codigo al mismo tiempo, evitando asi el paralelismo. Pero en este tp en especifico el server esta casi todo el tiempo haciendo operaciones I/O bound (lectura/escritura de socket), ya que espera bloqueado esperando que las agencias envien sus batches por la red. Si usamos threads, al bloquearse, el SO puede ceder el control a otro hilo para que procese otra conexion distinta, dando asi el casi pero muy cercano paralelismo.

Por ende, voy por el camino del multithreading, aunque no sea 100% paralelismo real (seria concurrente en todo caso), da la sensacion de serlo solo por la naturaleza del servidor (espera bloqueado la mayoria del tiempo esperando recibir algo del lado del cliente y responderle). 

Si hubiese otras operaciones que sea mas del estilo CPU bound (calculos matematicos por ejemplo), entonces ahi si me iria por el camino del multiprocessing. 

### Client

No hay cambios en el cliente, ya que la consigna se centra principalmente en el servidor.

---

### Server

Se agregaron mecanismos de **sincronización** para coordinar los hilos que manejan las conexiones con los clientes (*client handlers*).

Cada vez que llega un nuevo cliente, se lanza un thread (client handler) encargado de gestionar toda la comunicación con ese cliente en particular.

El hilo principal del servidor inicia el sorteo una vez que todos los clientes hayan enviado sus apuestas.

Una vez finalizado el sorteo, el hilo principal almacena los ganadores para que los client handlers puedan acceder a ellos y enviarlos a sus respectivos clientes.

Finalmente, cada *client handler* cierra su conexión, y el hilo principal realiza el *join* de todos los hilos, dando asi por terminado el servidor.

### Sincronización

En la implementación del servidor, existen dos recursos compartidos que deben protegerse:

**1. Agencias en espera de ganadores**

Cada *client handler* registra su agencia cuando recibe la consulta de ganadores. Como múltiples hilos pueden registrar simultáneamente, esto puede provocar inconsistencias.

Para resolverlo, se implementa un **`AgenciesMonitor`**, que:

- Encapsula las agencias en espera (un diccionario).
- Utiliza un *lock* para garantizar acceso seguro.
- Provee el metodo para registrar agencias de manera sincronizada.
- Cuenta con mas metodos propios de las agencias que no necesitan ser protegidos.

**2. Almacenamiento de apuestas**

Cada *client handler* guarda las apuestas a medida que las recibe. Si varios hilos escriben al mismo tiempo, podrían perderse datos.

Para evitar esto, se implementa un **`StorageMonitor`**, que:

- Provee un método para guardar apuestas de forma segura usando *lock*.
- Incluye un método de lectura que no requiere sincronización, ya que solo lo utiliza el hilo principal.

--- 

Además de proteger recursos, es necesario sincronizar el flujo de ejecución de los hilos.

**Barrera 1: Inicio del sorteo**

Se utiliza una *barrier* para sincronizar el punto en el que todos los clientes terminaron de enviar sus apuestas:

- El hilo principal espera a todos los *client handlers* antes de iniciar el sorteo.
- Cada *client handler*, luego de registrar su agencia, espera en la barrera.

**Barrera 2: Disponibilidad de resultados**

Luego de iniciado el sorteo, los *client handlers* deben esperar a que los resultados estén disponibles:

- Los *client handlers* esperan en una segunda barrera antes de acceder a los ganadores.
- El hilo principal, una vez finalizado el sorteo, guarda los resultados y también espera en la barrera.

Esto garantiza que ningún hilo intente acceder a resultados antes de que estén listos.