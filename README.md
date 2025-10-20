# HackNova--Synkro
Una pagina para poder guardar documentos pdf, leerlos, filtralos, poder etiquetarlos y filtrarlos para poder tener un mejor orden 

SYNKRO 
                                                                             
                                                                     


El capitolio nos ha solicitado crear una página web  la cual tendrá como utilidad almacenar, cargar, leer archivos PDF, etiquetar manualmente y sugerir automáticamente las etiquetas, el lenguaje que se usará para crear la página será HTML, 
Para la base de datos del proyecto se utilizará SQLite, una biblioteca de software integrada que permite gestionar la información de manera ligera y eficiente. Este sistema se caracteriza porque toda la base de datos se almacena en un único archivo dentro del disco duro del servidor, lo que facilita su mantenimiento y portabilidad.
En el caso de nuestra aplicación web, SQLite servirá para guardar los registros relacionados con los archivos cargados por los usuarios, incluyendo información como el nombre del archivo, las etiquetas asociadas, la fecha de creación o modificación. De esta forma, se podrá realizar una gestión ordenada y rápida de los datos, optimizando las búsquedas y la visualización dentro de la página.
El archivo PDF, por su parte, se guardará directamente en el sistema de archivos del servidor o, si se requiere mayor escalabilidad, en un servicio de almacenamiento en la nube. Gracias a la estructura de la base de datos, los usuarios podrán consultar, modificar o eliminar tanto los archivos como las carpetas asociadas desde la interfaz web, garantizando así una administración sencilla y dinámica de la información.
Además, SQLite ofrece un excelente rendimiento en operaciones de lectura, lo que resulta ideal para una página donde los usuarios acceden constantemente a los datos, etiquetas y fechas de los documentos. Esto asegura que la navegación sea fluida y que las consultas se procesen de forma casi inmediata, mejorando la experiencia general del usuario.
Posteriormente, se desarrolló la parte del sistema correspondiente al registro de usuarios, lo que permite que cada persona tenga acceso personalizado a la plataforma. Una vez que el usuario se registra o inicia sesión, puede visualizar toda la información almacenada anteriormente en la base de datos, incluyendo los archivos con sus etiquetas y fechas. Esto garantiza un entorno más seguro y organizado, donde cada usuario puede gestionar sus propios documentos, subir nuevos archivos, o eliminar aquellos que ya no sean necesarios.
