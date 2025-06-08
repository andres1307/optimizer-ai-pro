import os
import shutil
import tempfile
from tqdm import tqdm
import time
import fnmatch
import ctypes
from typing import List

class Cleaner:
    def __init__(self):
        # Directorios excluidos por seguridad
        self.excluded_dirs = {
            os.path.join(tempfile.gettempdir(), 'important'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Prefetch', 'Critical'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Temp', 'SystemLogs'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32'),
            os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files')),
            os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'))
        }
        
        # Patrones de archivos excluidos
        self.excluded_patterns = [
            '*.dll', '*.exe', '*.sys', '*.bat',
            '*.tmp', '*.log', '*.db', '*.dat',
            '*.mkd', '*.ps1', '*.vbs', '*.js'
        ]

    def is_file_locked(self, filepath):
        """Verifica si un archivo está en uso (Windows)"""
        if os.name != 'nt':
            return False
            
        try:
            handle = ctypes.windll.kernel32.CreateFileW(
                filepath,
                0x80000000,  # GENERIC_READ
                1,           # FILE_SHARE_READ
                None,
                3,           # OPEN_EXISTING
                0x80,        # FILE_ATTRIBUTE_NORMAL
                None
            )
            
            if handle == -1:
                return True
                
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        except:
            return True

    def should_skip(self, path):
        """Determina si un archivo/directorio debe ser excluido"""
        path_lower = path.lower()
        
        # Verificar directorios excluidos
        for excluded_dir in self.excluded_dirs:
            if excluded_dir.lower() in path_lower:
                return True
                
        # Verificar patrones de archivos
        filename = os.path.basename(path)
        if any(fnmatch.fnmatch(filename.lower(), pattern.lower()) 
               for pattern in self.excluded_patterns):
            return True
            
        # Verificar archivos en uso
        if os.path.isfile(path) and self.is_file_locked(path):
            return True
            
        return False

    def clean_temp_files(self):
        """Limpieza principal de archivos temporales"""
        print("\n🔧 Iniciando limpieza de archivos temporales...\n")

        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            print(f"⚠️ Directorio temporal no encontrado: {temp_dir}")
            return

        files_to_delete = []
        dirs_to_delete = []

        # Recopilar archivos y directorios
        for root, dirs, files in os.walk(temp_dir):
            # Filtrar directorios excluidos
            dirs[:] = [d for d in dirs if not self.should_skip(os.path.join(root, d))]
            
            for f in files:
                file_path = os.path.join(root, f)
                if not self.should_skip(file_path):
                    files_to_delete.append(file_path)
                    
            for d in dirs:
                dir_path = os.path.join(root, d)
                if not self.should_skip(dir_path):
                    dirs_to_delete.append(dir_path)

        total_items = len(files_to_delete) + len(dirs_to_delete)
        if total_items == 0:
            print("✅ No hay archivos temporales para limpiar")
            return

        deleted_files = 0
        deleted_dirs = 0

        # Proceso de limpieza con barra de progreso
        with tqdm(total=total_items, desc="🧹 Limpiando", ncols=100, 
                 bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}") as pbar:
            
            # Eliminar archivos
            for file_path in files_to_delete:
                try:
                    if not self.should_skip(file_path):
                        os.remove(file_path)
                        deleted_files += 1
                except Exception as e:
                    print(f"❌ No se pudo eliminar archivo: {file_path} | Error: {e}")
                finally:
                    pbar.update(1)

            # Eliminar directorios vacíos
            for dir_path in dirs_to_delete:
                try:
                    if not os.listdir(dir_path):
                        shutil.rmtree(dir_path)
                        deleted_dirs += 1
                except Exception as e:
                    print(f"❌ No se pudo eliminar carpeta: {dir_path} | Error: {e}")
                finally:
                    pbar.update(1)

        # Resultados
        print("\n✅ Limpieza completada.")
        print(f"📂 Archivos eliminados: {deleted_files}")
        print(f"📂 Carpetas eliminadas: {deleted_dirs}")
        print("✨ Todos los archivos temporales posibles han sido eliminados.")
        print("🔖 Creado por ISAMEL TRUJILLO\n")
        time.sleep(1)

    def clean_directory(self, target_path: str) -> int:
        """
        Limpieza genérica de directorios
        Devuelve el número de elementos eliminados
        """
        if not os.path.exists(target_path):
            print(f"⚠️ Ruta no existe: {target_path}")
            return 0
            
        if self.should_skip(target_path):
            print(f"⚠️ Ruta excluida: {target_path}")
            return 0
            
        return self._clean_directory(target_path)

    def _clean_directory(self, dir_path: str) -> int:
        """Lógica interna de limpieza"""
        deleted = 0
        try:
            for root, dirs, files in os.walk(dir_path, topdown=False):
                # Filtrar directorios
                dirs[:] = [d for d in dirs if not self.should_skip(os.path.join(root, d))]
                
                # Eliminar archivos
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self.should_skip(file_path):
                        try:
                            os.remove(file_path)
                            deleted += 1
                        except Exception as e:
                            print(f"❌ Error eliminando {file_path}: {str(e)}")
                
                # Eliminar directorios vacíos
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if not self.should_skip(dir_path):
                        try:
                            if not os.listdir(dir_path):
                                shutil.rmtree(dir_path)
                                deleted += 1
                        except Exception as e:
                            print(f"❌ Error eliminando {dir_path}: {str(e)}")
        except Exception as e:
            print(f"❌ Error crítico: {str(e)}")
        
        return deleted

    def clean_windows_temp(self) -> None:
        """Limpieza específica del directorio Temp de Windows"""
        win_temp = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Temp')
        if os.path.exists(win_temp):
            deleted = self._clean_directory(win_temp)
            print(f"✅ Eliminados {deleted} elementos de {win_temp}")
        else:
            print(f"⚠️ No se encontró Windows Temp en {win_temp}")