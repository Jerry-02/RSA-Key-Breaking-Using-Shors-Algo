import subprocess
libraries = ["qiskit", "rsa","numpy","tkinter"]

for library in libraries:
    # Run the installation command for each library
    subprocess.run(["pip", "install", library])
    
    
import streamlit as st
import numpy as np
import qiskit
from math import sqrt, log, gcd
import random
from random import randint
import rsa
from qiskit import *
from tkinter import *
from tkinter import simpledialog
from tkinter import simpledialog, messagebox

st.title('''Decrypting a 4-bit RSA encrypted password using Shor's Algorithm''')


def mod_inverse(a, m):
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return -1

def isprime(n):
    if n < 2:
        return False
    elif n == 2:
        return True
    else:
        for i in range(1, int(sqrt(n)) + 1):
            if n % i == 0:
                return False
    return True


def generate_keypair(keysize):
    p = randint(1, 1000)
    q = randint(1, 1000)
    nMin = 1 << (keysize - 1)
    nMax = (1 << keysize) - 1
    primes = [2]
    start = 1 << (keysize // 2 - 1)
    stop = 1 << (keysize // 2 + 1)
    if start >= stop:
        return []
    for i in range(3, stop + 1, 2):
        for p in primes:
            if i % p == 0:
                break
        else:
            primes.append(i)
    while (primes and primes[0] < start):
        del primes[0]
    # Select two random prime numbers p and q
    while primes:
        p = random.choice(primes)
        primes.remove(p)
        q_values = [q for q in primes if nMin <= p * q <= nMax]
        if q_values:
            q = random.choice(q_values)
            break
    # Calculate n
    n = p * q
    # Calculate phi
    phi = (p - 1) * (q - 1)
    # Select e
    e = random.randrange(1, phi)
    g = gcd(e, phi)
    # Calculate d
    while True:
        e = random.randrange(1, phi)
        g = gcd(e, phi)
        d = mod_inverse(e, phi)
        if g == 1 and e != d:
            break

    return ((e, n), (d, n))


def encrypt(plaintext, package):
    e, n = package
    ciphertext = [pow(ord(c), e, n) for c in plaintext]
    return ''.join(map(lambda x: str(x), ciphertext)), ciphertext


def period(a,N):
    qasm_sim = qiskit.Aer.get_backend('qasm_simulator')
    available_qubits = 16 
    r=-1   
    
    if N >= 2**available_qubits:
        print(str(N)+' is too big for IBMQX')
    
    qr = QuantumRegister(available_qubits)   
    cr = ClassicalRegister(available_qubits)
    qc = QuantumCircuit(qr,cr)
    x0 = randint(1, N-1) 
    x_binary = np.zeros(available_qubits, dtype=bool)
    
    for i in range(1, available_qubits + 1):
        bit_state = (N%(2**i)!=0)
        if bit_state:
            N -= 2**(i-1)
        x_binary[available_qubits-i] = bit_state    
    
    for i in range(0,available_qubits):
        if x_binary[available_qubits-i-1]:
            qc.x(qr[i])
    x = x0
    
    while np.logical_or(x != x0, r <= 0):
        r+=1
        qc.measure(qr, cr) 
        for i in range(0,3): 
            qc.x(qr[i])
        qc.cx(qr[2],qr[1])
        qc.cx(qr[1],qr[2])
        qc.cx(qr[2],qr[1])
        qc.cx(qr[1],qr[0])
        qc.cx(qr[0],qr[1])
        qc.cx(qr[1],qr[0])
        qc.cx(qr[3],qr[0])
        qc.cx(qr[0],qr[1])
        qc.cx(qr[1],qr[0])
        
        result = execute(qc,backend = qasm_sim, shots=1024).result()
        counts = result.get_counts()
        
        results = [[],[]]
        for key,value in counts.items(): 
            results[0].append(key)
            results[1].append(int(value))
        s = results[0][np.argmax(np.array(results[1]))]
    return r


def shors_breaker(N):
    N = int(N)
    while True:
        a=randint(0,N-1)
        g=gcd(a,N)
        if g!=1 or N==1:
            return g,N//g
        else:
            r=period(a,N) 
            if r % 2 != 0:
                continue
            elif pow(a,r//2,N)==-1:
                continue
            else:
                p=gcd(pow(a,r//2)+1,N)
                q=gcd(pow(a,r//2)-1,N)
                if p==N or q==N:
                    continue
                return p,q
            
            
def modular_inverse(a,m): 
    a = a % m; 
    for x in range(1, m) : 
        if ((a * x) % m == 1) : 
            return x 
    return 1


def decrypt(ciphertext, package):
    d, n = package
    plaintext = [chr(pow(c, d, n)) for c in ciphertext]
    return (''.join(plaintext))


def main():
    bit_length = 4
    public_k, private_k = generate_keypair(2 ** bit_length)


    # plain_txt = simpledialog.askstring("Input", "Enter a message:", show='*')
    plain_txt = st.text_input("Enter a message:",type="password")
    button1 = st.button("ok")
    # root.destroy()  # Close the hidden window after input
    
    if button1:
        cipher_txt, cipher_obj = encrypt(plain_txt, public_k)
        st.write("Encrypted Message,", "Encrypted message: {}".format(cipher_txt))
        # messagebox.showinfo("Encrypted Message", "Encrypted message: {}".format(cipher_txt))

        N_shor = public_k[1]
        assert N_shor > 0, "Input must be positive"
        p, q = shors_breaker(N_shor)
        phi = (p - 1) * (q - 1)
        d_shor = modular_inverse(public_k[0], phi)

        decrypted_msg = decrypt(cipher_obj, (d_shor, N_shor))
        st.write("Decrypted Message", 'Message Cracked using Shor\'s Algorithm: {} '.format(decrypted_msg))
        # messagebox.showinfo("Decrypted Message", 'Message Cracked using Shor\'s Algorithm: {} '.format(decrypted_msg))
        
        # root.mainloop()


if __name__ == "__main__":
    root = Tk()
    root.withdraw()  # Hide the main window
    main()
