# eval/scenarios.py
# Escenarios de evaluación orientados a conversaciones reales:
# - contradicciones y correcciones del usuario
# - información obsoleta
# - ruido e interrupciones
# - preguntas irrelevantes
# - casos donde la memoria ayuda poco o nada

scenarios = [
    # Estructura de cada escenario:
    # - scenario_id: identificador único
    # - category: tipo de dificultad conversacional
    # - memory_advantage_expected: expectativa teórica de ventaja de memoria
    # - messages: secuencia multivuelta usuario
    # - expected_behavior: criterio narrativo de éxito
    # - checks: reglas objetivas para score automático
    {
        "scenario_id": "preferencia_contacto_contradiccion",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Prefiero que me contacten por correo.",
            "Corrijo: a partir de ahora prefiero llamadas por teléfono.",
            "¿Cuál es mi canal de contacto preferido actualmente?"
        ],
        "expected_behavior": "Debe priorizar la preferencia más reciente (teléfono).",
        "checks": {
            "last_response_must_include_any": ["teléfono", "telefono", "llamada"],
            "last_response_must_not_include_any": ["correo como preferencia actual"]
        }
    },
    {
        "scenario_id": "correo_actualizado",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Mi correo es ana@empresa.com.",
            "Actualización: usa mejor ana.nuevo@empresa.com.",
            "¿Qué correo debo usar para contactarme?"
        ],
        "expected_behavior": "Debe usar el correo más reciente.",
        "checks": {
            "last_response_must_include_any": ["ana.nuevo@empresa.com"],
            "last_response_must_not_include_any": ["ana@empresa.com"]
        }
    },
    {
        "scenario_id": "direccion_entrega_corregida",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Envía el pedido a Calle 10 #45-22.",
            "Me equivoqué, la dirección correcta es Calle 80 #12-08.",
            "¿A qué dirección debe ir el envío?"
        ],
        "expected_behavior": "Debe mantener la dirección corregida.",
        "checks": {
            "last_response_must_include_any": ["Calle 80 #12-08", "80 #12-08"],
            "last_response_must_not_include_any": ["Calle 10 #45-22"]
        }
    },
    {
        "scenario_id": "pedido_corregido_numero",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Mi pedido es #12345.",
            "No, perdón, el número correcto es #12346.",
            "¿Cuál es mi número de pedido actual?"
        ],
        "expected_behavior": "Debe conservar el pedido más reciente.",
        "checks": {
            "last_response_must_include_any": ["12346"],
            "last_response_must_not_include_any": ["12345"]
        }
    },
    {
        "scenario_id": "preferencia_revertida_sms_a_correo",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Prefiero notificaciones por SMS.",
            "Olvida eso, ahora solo por correo electrónico.",
            "¿Qué canal debo usar para tus notificaciones?"
        ],
        "expected_behavior": "Debe respetar la última corrección.",
        "checks": {
            "last_response_must_include_any": ["correo", "correo electrónico"],
            "last_response_must_not_include_any": ["sms como canal actual"]
        }
    },
    {
        "scenario_id": "pedido_obsoleto_cancelado",
        "category": "obsoleto",
        "memory_advantage_expected": "high",
        "messages": [
            "El pedido #88888 estaba en tránsito.",
            "Actualización: ese pedido ya fue cancelado.",
            "¿Cuál es el estado actual del pedido #88888?"
        ],
        "expected_behavior": "Debe considerar obsoleta la información anterior.",
        "checks": {
            "last_response_must_include_any": ["cancelado", "cancelada"],
            "last_response_must_not_include_any": ["en tránsito", "en transito"]
        }
    },
    {
        "scenario_id": "pedido_obsoleto_entregado",
        "category": "obsoleto",
        "memory_advantage_expected": "high",
        "messages": [
            "Ayer dijimos que mi pedido #33333 estaba retrasado.",
            "Actualización de hoy: ya fue entregado.",
            "¿En qué estado está ahora mismo?"
        ],
        "expected_behavior": "Debe responder con el estado más reciente.",
        "checks": {
            "last_response_must_include_any": ["entregado", "entrega"],
            "last_response_must_not_include_any": ["retrasado"]
        }
    },
    {
        "scenario_id": "reclamo_resuelto",
        "category": "obsoleto",
        "memory_advantage_expected": "medium",
        "messages": [
            "Tengo un reclamo abierto por cobro duplicado.",
            "Ya me confirmaron que el reclamo fue resuelto.",
            "¿Sigo teniendo el reclamo abierto?"
        ],
        "expected_behavior": "Debe reconocer que el estado actual es resuelto.",
        "checks": {
            "last_response_must_include_any": ["resuelto", "cerrado", "solucionado"],
            "last_response_must_not_include_any": ["abierto"]
        }
    },
    {
        "scenario_id": "dos_pedidos_similares_no_confundir",
        "category": "similar",
        "memory_advantage_expected": "high",
        "messages": [
            "Tengo dos pedidos: #55555 y #55556.",
            "El #55555 fue cancelado.",
            "¿Qué sabes del #55556?"
        ],
        "expected_behavior": "Debe evitar mezclar datos de entidades similares.",
        "checks": {
            "last_response_must_include_any": ["55556"],
            "last_response_must_not_include_any": ["#55555 fue cancelado"]
        }
    },
    {
        "scenario_id": "referencia_ambiguo_el_otro",
        "category": "similar",
        "memory_advantage_expected": "medium",
        "messages": [
            "El pedido #11111 llegó.",
            "El pedido #22222 sigue en tránsito.",
            "¿Y el otro?"
        ],
        "expected_behavior": "Debe pedir aclaración ante ambigüedad.",
        "checks": {
            "last_response_must_include_any": ["aclar", "confirm", "especific", "¿a cuál", "te refieres"],
            "must_ask_question": True
        }
    },
    {
        "scenario_id": "ruido_intermedio_y_recuperacion",
        "category": "ruido",
        "memory_advantage_expected": "high",
        "messages": [
            "Prefiero atención por WhatsApp.",
            "¿Cuál es tu película favorita?",
            "Cuéntame un dato curioso.",
            "Por cierto, ¿cómo prefiero que me atiendan?"
        ],
        "expected_behavior": "Debe mantener hechos relevantes pese al ruido.",
        "checks": {
            "last_response_must_include_any": ["whatsapp"],
            "last_response_must_not_include_any": ["película favorita"]
        }
    },
    {
        "scenario_id": "interrupcion_chitchat_en_reclamo",
        "category": "ruido",
        "memory_advantage_expected": "medium",
        "messages": [
            "Quiero presentar un reclamo por demoras.",
            "Antes, cuéntame un chiste corto.",
            "Retomando, ¿qué datos necesitas para mi reclamo?"
        ],
        "expected_behavior": "Debe retomar el hilo del reclamo tras la interrupción.",
        "checks": {
            "last_response_must_include_any": ["número de pedido", "descripción", "desde cuándo", "reclamo"]
        }
    },
    {
        "scenario_id": "consulta_irrelevante_tras_pedido",
        "category": "irrelevante",
        "memory_advantage_expected": "low",
        "messages": [
            "Mi pedido es #99999.",
            "Ahora dime un chiste de oficina.",
            "Solo el chiste, sin hablar del pedido."
        ],
        "expected_behavior": "No debería arrastrar memoria innecesaria al responder chitchat.",
        "checks": {
            "last_response_must_include_any": ["jaja", "chiste", "grac"],
            "last_response_must_not_include_any": ["99999"]
        }
    },
    {
        "scenario_id": "smalltalk_puro",
        "category": "irrelevante",
        "memory_advantage_expected": "none",
        "messages": [
            "Hola, ¿cómo estás?",
            "¿Puedes contarme algo interesante?",
            "Gracias."
        ],
        "expected_behavior": "Escenario neutral donde la memoria no debería aportar ventaja clara.",
        "checks": {
            "last_response_must_include_any": ["de nada", "ayudarte", "gracias"]
        }
    },
    {
        "scenario_id": "canal_contacto_con_negacion",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "No me llames por la mañana.",
            "Cambio: sí puedes llamarme por la mañana.",
            "¿Pueden llamarme en la mañana o no?"
        ],
        "expected_behavior": "Debe respetar la instrucción más reciente incluso si contradice la inicial.",
        "checks": {
            "last_response_must_include_any": ["sí", "si", "pueden llamarte"],
            "last_response_must_not_include_any": ["no me llames por la mañana"]
        }
    },
    {
        "scenario_id": "nombre_preferido_actual",
        "category": "contradiccion",
        "memory_advantage_expected": "high",
        "messages": [
            "Llámame Carlos.",
            "Mejor dime Carlitos.",
            "¿Cómo debo llamarte?"
        ],
        "expected_behavior": "Debe usar el alias actualizado.",
        "checks": {
            "last_response_must_include_any": ["carlitos"],
            "last_response_must_not_include_any": ["carlos"]
        }
    },
    {
        "scenario_id": "idioma_preferido_actual",
        "category": "contradiccion",
        "memory_advantage_expected": "medium",
        "messages": [
            "Respóndeme en español.",
            "En realidad prefiero inglés.",
            "¿En qué idioma debo responderte ahora?"
        ],
        "expected_behavior": "Debe priorizar la preferencia más reciente.",
        "checks": {
            "last_response_must_include_any": ["inglés", "ingles", "english"],
            "last_response_must_not_include_any": ["español como preferencia actual"]
        }
    },
    {
        "scenario_id": "pregunta_general_neutral",
        "category": "neutral",
        "memory_advantage_expected": "none",
        "messages": [
            "¿Cuáles son sus horarios de atención?"
        ],
        "expected_behavior": "Caso de control con una sola consulta general.",
        "checks": {
            "last_response_must_include_any": ["horario", "atención", "atencion", "lunes", "viernes"]
        }
    },
    {
        "scenario_id": "doble_pedido_uno_entregado_otro_no",
        "category": "similar",
        "memory_advantage_expected": "high",
        "messages": [
            "Tengo las órdenes #70001 y #70002.",
            "La #70001 ya fue entregada.",
            "¿Qué pasa con la #70002?"
        ],
        "expected_behavior": "Debe responder sin trasladar estado de una orden a otra.",
        "checks": {
            "last_response_must_include_any": ["70002"],
            "last_response_must_not_include_any": ["70001 ya fue entregada"]
        }
    },
    {
        "scenario_id": "preferencia_con_ruido_largo",
        "category": "ruido",
        "memory_advantage_expected": "high",
        "messages": [
            "Mi canal favorito es correo.",
            "¿Qué opinas del clima?",
            "¿Conoces una receta rápida?",
            "¿Cuál era mi canal favorito al final?"
        ],
        "expected_behavior": "Debe recuperar el hecho útil tras varios turnos irrelevantes.",
        "checks": {
            "last_response_must_include_any": ["correo"],
            "last_response_must_not_include_any": ["clima como preferencia", "receta como preferencia"]
        }
    }
]
