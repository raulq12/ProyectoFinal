import subprocess
import sys
import platform
import os
import shutil

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    @staticmethod
    def use_colors():
        # En Windows, los colores ANSI solo funcionan en terminales modernas o con módulos especiales
        return platform.system() != "Windows" or "ANSICON" in os.environ

def print_error(message):
    if Colors.use_colors():
        print(f"{Colors.RED}Error: {message}{Colors.RESET}", file=sys.stderr)
    else:
        print(f"Error: {message}", file=sys.stderr)

def print_success(message):
    if Colors.use_colors():
        print(f"{Colors.GREEN}Éxito: {message}{Colors.RESET}")
    else:
        print(f"Éxito: {message}")

def print_info(message):
    if Colors.use_colors():
        print(f"{Colors.BLUE}Info: {message}{Colors.RESET}")
    else:
        print(f"Info: {message}")

def print_warning(message):
    if Colors.use_colors():
        print(f"{Colors.YELLOW}Advertencia: {message}{Colors.RESET}")
    else:
        print(f"Advertencia: {message}")

def run_command(command, error_message):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{error_message}: {e}")
        return False

def is_windows():
    return platform.system() == "Windows"

def is_package_installed(package_name):
    """Verifica si un paquete del sistema está instalado"""
    if is_windows():
        # En Windows no usamos dpkg, así que asumimos que no está instalado
        # y lo manejaremos de otra manera
        return False
    else:
        try:
            subprocess.run(
                f"dpkg -l {package_name}",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except subprocess.CalledProcessError:
            return False

def is_nmap_installed():
    """Verifica si nmap está instalado en cualquier sistema operativo"""
    # Primero intentamos encontrar nmap en el PATH
    nmap_in_path = shutil.which("nmap")
    if nmap_in_path:
        return True
    
    # Si no está en el PATH, buscamos en ubicaciones comunes en Windows
    if is_windows():
        common_paths = [
            "C:\\Program Files (x86)\\Nmap\\nmap.exe",
            "C:\\Program Files\\Nmap\\nmap.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                # Si encontramos nmap, lo añadimos al PATH para futuras referencias
                os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.path.dirname(path)
                print_info(f"Nmap encontrado en {path} y añadido al PATH.")
                return True
    
    # Como último recurso, intentamos ejecutar nmap
    try:
        subprocess.run(
            "nmap --version",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_python_nmap_compatibility():
    """Verifica si python-nmap puede funcionar con la instalación de nmap"""
    try:
        import nmap
        scanner = nmap.PortScanner()
        # Intentamos una operación simple para verificar la compatibilidad
        scanner.scan('127.0.0.1', '22-80')
        return True
    except Exception as e:
        print_warning(f"python-nmap está instalado pero puede haber problemas de compatibilidad: {e}")
        return True  # Devolvemos True de todos modos para continuar

def install_system_dependencies():
    """Instala dependencias del sistema según el sistema operativo"""
    if is_windows():
        # En Windows, verificamos nmap
        if not is_nmap_installed():
            print_info("Nmap no está instalado en Windows o no está en el PATH del sistema.")
            print_info("Por favor, descarga e instala Nmap desde: https://nmap.org/download.html")
            print_info("Asegúrate de marcar la opción para añadir Nmap al PATH durante la instalación.")
            response = input("¿Deseas continuar con la instalación de los paquetes de Python? (s/n): ")
            if response.lower() != 's':
                sys.exit(1)
        else:
            print_info("Nmap está instalado en Windows.")
    else:
        # En Linux/Unix
        packages = ["nmap", "python3-pip"]
        needs_update = False

        # Verificar si falta algún paquete
        for package in packages:
            if not is_package_installed(package):
                print_info(f"{package} no está instalado. Se instalará.")
                needs_update = True

        # Actualizar e instalar solo si es necesario
        if needs_update:
            print_info("Actualizando lista de paquetes...")
            if not run_command(
                "sudo apt update",
                "Fallo al actualizar la lista de paquetes"
            ):
                sys.exit(1)

            for package in packages:
                if not is_package_installed(package):
                    print_info(f"Instalando {package}...")
                    if not run_command(
                        f"sudo apt install -y {package}",
                        f"Fallo al instalar {package}"
                    ):
                        sys.exit(1)
        else:
            print_info("Todos los paquetes del sistema están instalados.")

def is_pip_available():
    """Verifica si pip está disponible para Python 3"""
    try:
        python_cmd = "python" if is_windows() else "python3"
        subprocess.run(
            f"{python_cmd} -m pip --version",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def is_python_package_installed(package_name):
    """Verifica si un paquete de Python está instalado"""
    try:
        # Primero intentamos importar el módulo directamente
        if package_name == "python-nmap":
            try:
                import nmap
                return True
            except ImportError:
                pass
        elif package_name == "scapy":
            try:
                import scapy
                return True
            except ImportError:
                pass
        elif package_name == "keyboard":
            try:
                import keyboard
                return True
            except ImportError:
                pass
        elif package_name == "netifaces":
            try:
                import netifaces
                return True
            except ImportError:
                pass
        
        # Si no se puede importar, verificamos con pip
        python_cmd = "python" if is_windows() else "python3"
        subprocess.run(
            f"{python_cmd} -m pip show {package_name}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_python_packages():
    """Instala paquetes de Python globalmente si no están instalados"""
    python_cmd = "python" if is_windows() else "python3"
    
    # Primero verificar si pip está disponible
    if not is_pip_available():
        if is_windows():
            print_info("pip no está disponible. Instalando pip...")
            # En Windows, descargamos get-pip.py
            if not run_command(
                "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && " + 
                f"{python_cmd} get-pip.py",
                "Fallo al instalar pip"
            ):
                sys.exit(1)
        else:
            print_info("pip no está disponible. Instalando python3-pip...")
            if not run_command(
                "sudo apt update && sudo apt install -y python3-pip",
                "Fallo al instalar python3-pip"
            ):
                sys.exit(1)
    
    # Lista actualizada de paquetes incluyendo netifaces
    packages = ["python-nmap", "scapy", "keyboard", "netifaces"]
    needs_install = False

    # Verificar si falta algún paquete de Python
    for package in packages:
        if not is_python_package_installed(package):
            print_info(f"{package} no está instalado. Se instalará.")
            needs_install = True

    # Instalar solo si es necesario
    if needs_install:
        print_info("Instalando paquetes de Python...")
        
        # En Windows, verificar si tenemos las herramientas de compilación para netifaces
        if is_windows() and not is_python_package_installed("netifaces"):
            print_info("El paquete netifaces requiere herramientas de compilación en Windows.")
            print_info("Intentando instalar una versión precompilada...")
            
            # Intentar instalar wheel precompilado si está disponible
            try:
                # Determinar la versión de Python y arquitectura
                python_version = platform.python_version()[:3].replace(".", "")
                architecture = "win32" if platform.architecture()[0] == "32bit" else "win_amd64"
                
                # Intentar instalar con pip directamente primero
                cmd = f"{python_cmd} -m pip install netifaces"
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    print_success("netifaces instalado correctamente.")
                except subprocess.CalledProcessError:
                    print_warning("No se pudo instalar netifaces directamente.")
                    print_info("Es posible que necesites instalar Visual C++ Build Tools.")
                    print_info("Visita: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
                    print_info("Durante la instalación, selecciona 'Desarrollo de escritorio con C++'")
                    
                    # Preguntar si desea continuar sin netifaces
                    response = input("¿Deseas continuar sin instalar netifaces? (s/n): ")
                    if response.lower() != 's':
                        sys.exit(1)
            except Exception as e:
                print_error(f"Error al instalar netifaces: {e}")
                print_info("Es posible que necesites instalar Visual C++ Build Tools.")
                print_info("Visita: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
                
                # Preguntar si desea continuar sin netifaces
                response = input("¿Deseas continuar sin instalar netifaces? (s/n): ")
                if response.lower() != 's':
                    sys.exit(1)
        
        # Instalar los demás paquetes uno por uno
        for package in packages:
            # Saltamos netifaces en Windows si ya lo intentamos instalar arriba
            if is_windows() and package == "netifaces":
                continue
                
            if not is_python_package_installed(package):
                print_info(f"Instalando {package}...")
                cmd = f"{python_cmd} -m pip install {package}"
                try:
                    subprocess.run(cmd, shell=True, check=True)
                except subprocess.CalledProcessError:
                    # Si falla, intentamos con métodos alternativos según el sistema
                    if is_windows():
                        print_info(f"Reintentando instalar {package} con privilegios elevados...")
                        if not run_command(
                            f'powershell -Command "Start-Process \"{python_cmd}\" -ArgumentList \"-m pip install {package}\" -Verb RunAs"',
                            f"Fallo al instalar {package}"
                        ):
                            print_error(f"No se pudo instalar {package}. Intenta instalarlo manualmente.")
                            if package == "python-nmap":
                                print_info("Asegúrate de que Nmap esté instalado correctamente en tu sistema.")
                    else:
                        print_info(f"Reintentando instalar {package} con --break-system-packages...")
                        if not run_command(
                            f"{python_cmd} -m pip install --break-system-packages {package}",
                            f"Fallo al instalar {package}"
                        ):
                            print_error(f"No se pudo instalar {package}. Intenta instalarlo manualmente.")
    else:
        print_info("Todos los paquetes de Python están instalados.")
    
    # Verificar la compatibilidad de python-nmap con nmap
    if is_python_package_installed("python-nmap"):
        check_python_nmap_compatibility()

def main():
    try:
        print_info(f"Sistema operativo detectado: {platform.system()} {platform.version()}")
        print_info(f"Python: {platform.python_version()}")
        
        # Forzar la detección de nmap al inicio
        if is_nmap_installed():
            print_info("Nmap está instalado y disponible en el sistema.")
        else:
            print_info("Nmap no está instalado o no está disponible en el PATH.")
        
        # Instalar dependencias del sistema (si es necesario)
        install_system_dependencies()

        # Instalar paquetes de Python (si es necesario)
        install_python_packages()

        print_success("¡Todas las dependencias están instaladas correctamente!")

    except Exception as e:
        print_error(f"Error crítico: {e}")
        if is_windows():
            input("Presiona Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()
