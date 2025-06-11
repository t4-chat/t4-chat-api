from fastapi import FastAPI
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from src.config import settings

def _create_resource():
    return Resource.create({
        ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME,
        ResourceAttributes.SERVICE_VERSION: settings.VERSION,
    })

def _setup_tracing(resource: Resource):        
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True
        )
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return provider

def _setup_metrics(resource: Resource):
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True
        )
    )
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return provider

def configure_telemetry(app: FastAPI):
    resource = _create_resource()
    _setup_tracing(resource)
    _setup_metrics(resource)

    FastAPIInstrumentor.instrument_app(app)
    return app
