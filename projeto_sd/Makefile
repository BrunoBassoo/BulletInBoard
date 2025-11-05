CC = gcc
CFLAGS = -Wall -Wextra -pthread
LIBS = -lzmq -lmsgpackc -lpthread -lm

all: cliente

cliente: cliente.c
	$(CC) $(CFLAGS) -o cliente cliente.c $(LIBS)

clean:
	rm -f cliente

.PHONY: all clean

