# Oscar

Modern show automation software systems such as [Qlab](https://figure53.com/qlab/) support the use of the [Open Sound Control] protocol to communicate with, and automate external devices. Unfortunately however, many hardware devices used the professional broadcast and events industry do not support OSC directly. To overcome this, OSCar is designed to establish a connection to any device which accept TCP connections via an ethernet port, and forward messages recieved via OSC to the devices. 

Users must be aware of the required formatting of the messages, details of which are generally available from the hardware manuals, or directly from the manufacurers.

## Design principles

Oscar is designed in such a way that users input desired state, and Oscar asyncronously attempts to achieve that state in the background. This allows a seperation of concern from the front-end and the daemon, and allows Oscar to perform some tasks automatically, like attempt to recover from dropped connections.

## Requirements

* Pyhon 2.7
	* Django 1.8
	* gevent 1.0
	* celery 3.1
* RabbitMQ server (for commincation between front end and back end)

## Architecture

Oscar consists of a Django based web frontend and a Celery worker daemon as the backend. The two parts communicate via a RabbitMQ AMQP message server, however the communication is all handled by Celery.
The web front end is used to create definitions of hardware devices and their IP/port settings. The backend then gets notified of these definitions (and any changes) and establises the required connections to devices. The backend also runs the OSC server. All the connections are managed within lightweight green threads.

## Using Oscar

Oscar is considered alpha software so should not be used in critical situations as the only form of control. Deployment consists of running the Django interface via WSGI and a suitable web server (nginx, Apache, lighthtpd etc), a RabbitMQ server and a Celery process. Connections to devices can be established by accessing the Django web interface. Once devices are set up, messages can be routed to devices by sending OSC commands to /device/<device name>/message "<message>". 